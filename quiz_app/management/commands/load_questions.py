import json, os
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from quiz_app.models import Module, Question
class Command(BaseCommand):
    help = 'Load modules/questions from modules.json into DB'
    def add_arguments(self, parser):
        parser.add_argument('--file', type=str, default='modules.json', help='Path to JSON file')
    def handle(self, *args, **options):
        file_path = options['file']
        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f"{file_path} not found"))
            return
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        for module_data in data:
            name = module_data.get('module') or module_data.get('name')
            if not name:
                continue
            slug = slugify(name)
            module_obj, created = Module.objects.get_or_create(name=name, slug=slug)
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created module {name}"))
            for q in module_data.get('questions', []):
                text = q.get('question') or q.get('text')
                options = q.get('options', [])
                answer = q.get('answer')
                if isinstance(answer, str):
                    try:
                        answer_idx = options.index(answer)
                    except ValueError:
                        answer_idx = 0
                else:
                    answer_idx = int(answer or 0)
                if not Question.objects.filter(module=module_obj, text=text).exists():
                    Question.objects.create(module=module_obj, text=text, options=options, correct_index=answer_idx)
                    self.stdout.write(self.style.NOTICE(f"Added question to {name}: {text[:50]}"))
                else:
                    self.stdout.write(self.style.WARNING(f"Question exists in {name}: {text[:50]}"))
        self.stdout.write(self.style.SUCCESS('Done loading questions.'))
