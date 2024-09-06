from django.shortcuts import render, redirect
from .forms import QuizForm
import json
import requests

def convert_to_special_format(json_data):
    output = "<|begin_of_text|>"
    for entry in json_data:
        if entry["role"] == "system":
            output += f'<|start_header_id|>system<|end_header_id|>\n\n{entry["content"]}<|eot_id|>'
        elif entry["role"] == "user":
            output += f'\n<|start_header_id|>{entry["role"]}<|end_header_id|>\n\n{entry["content"]}<|eot_id|>'
            if json_data.index(entry) != len(json_data) - 1:
                output += ""
        elif entry["role"] == "assistant":
            output += f'\n<|start_header_id|>{entry["role"]}<|end_header_id|>\n\n{entry["content"]}<|eot_id|>'

    output += "\n<|start_header_id|>assistant<|end_header_id|>"
    return output

def get_answer_question(text):
    url = "https://inference2.t3ai.org/v1/completions"

    json_data = [
        {"role": "system", "content": "Sen bir yardımcı sınav hazırlayıcısın ve Türkçe dilinde dört şıklı test soruları üretiyorsun. Verilen metinle ilgili çeşitli sorular oluşturup cevapları sağlıyorsun. Soruların, metnin farklı bölümlerini kapsamalı ve her biri benzersiz dört şık içermelidir. Sadece bir doğru cevap olmalıdır. Çıktıyı **kesinlikle** aşağıdaki JSON formatında döndürmelisin, başka kelimeler kullanmamalısın."},
        {"role": "user", "content": f"""
            Verilen metin üzerinden anlamlı ve çeşitli soru-cevaplar üretin. 
            Sorular metnin farklı bölümlerini kapsamalı ve her biri dört şıklı olmalıdır. 
            Her şık benzersiz olmalı ve yalnızca bir doğru cevap içermelidir.
            **Aşağıdaki JSON formatını birebir kullanın, key isimlerini değiştirmeyin**:

            <output>
            [
            {{
                "soru": "Osmanlı İmparatorluğu hangi yüzyılın başında kuruldu?",
                "seçenekler": {{
                "A": "14. yüzyıl",
                "B": "15. yüzyıl",
                "C": "16. yüzyıl",
                "D": "17. yüzyıl"
                }},
                "doğru_cevap": "B"
            }},
            {{
                "soru": "Osmanlı İmparatorluğu'nun başkenti hangi şehirdir?",
                "seçenekler": {{
                "A": "İstanbul",
                "B": "Ankara",
                "C": "İzmir",
                "D": "Antalya"
                }},
                "doğru_cevap": "A"
            }}
            ]
            <output>

            Yukarıdaki JSON formatı yalnızca örnek amaçlıdır. Üreteceğiniz sorular ve cevaplar, verilen metne uygun olmalıdır. **Format dışına çıkmadan, 'soru', 'seçenekler', ve 'doğru_cevap' key'lerini kullanarak** sorularınızı metinden türetin ve doğru cevapları buna göre belirleyin.

            Metin: {text}
        """}
    ]

    special_format_output = convert_to_special_format(json_data)


    payload = json.dumps({
    "model": "/home/ubuntu/hackathon_model_2/",
    "prompt": special_format_output,
    "temperature": 0.01,
    "top_p": 0.95,
    "max_tokens": 1024,
    "repetition_penalty": 1.1,
    "stop_token_ids": [
        128001,
        128009
    ],
    "skip_special_tokens": True
    })

    headers = {
    'Content-Type': 'application/json',
    }

    response = requests.post(url, headers=headers, data=payload)
    pretty_response = json.loads(response.text)

    return json.loads(pretty_response['choices'][0]['text'])

def generate_quiz(request):
    if request.method == 'POST':
        form = QuizForm(request.POST)
        if form.is_valid():
            text = form.cleaned_data['prompt']
            questions_answers = get_answer_question(text)
            print(questions_answers)
            quiz_data = []
            for qa in questions_answers:
                question_key = next((key for key in qa.keys() if key in ["soru", "question"]), None)
                question = qa[question_key] if question_key else "Soru bulunamadı"
                
                options_key = next((key for key in qa.keys() if key in ["seçenekler", "options"]), None)
                options = list(qa[options_key].values()) if options_key else []
                
                correct_answer_key = next((key for key in qa.keys() if key in ["doğru_cevap", "correct_answer"]), None)
                correct_answer = qa[options_key][qa[correct_answer_key]] if correct_answer_key and options_key else "Cevap bulunamadı"

                quiz_data.append({
                    'question': question,
                    'options': options,
                    'correct_answer': correct_answer
                })

            request.session['quiz_data'] = quiz_data
            return redirect('take_quiz')
    else:
        form = QuizForm()
    
    return render(request, 'prompt_form.html', {'form': form})

def take_quiz(request):
    quiz_data = request.session.get('quiz_data', [])
    if not quiz_data:
        return redirect('generate_quiz')  

    return render(request, 'quiz.html', {'quiz_data': quiz_data})

def check_quiz(request):
    if request.method == 'POST':
        quiz_data = request.session.get('quiz_data', [])
        total_questions = len(quiz_data)
        correct_count = 0

        user_answers = {}
        for i, item in enumerate(quiz_data, start=1):
            user_answer = request.POST.get(f'answer_{i}')
            correct_answer = item['correct_answer']
            user_answers[f'question_{i}'] = {
                'question': item['question'],
                'user_answer': user_answer,
                'correct_answer': correct_answer,
                'is_correct': user_answer == correct_answer
            }
            if user_answer == correct_answer:
                correct_count += 1

        score = int((correct_count / total_questions) * 100)

        context = {
            'user_answers': user_answers,
            'score': score,
            'total_questions': total_questions,
            'correct_count': correct_count,
        }

        return render(request, 'result.html', context)
    else:
        return redirect('take_quiz')
