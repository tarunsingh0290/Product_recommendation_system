from app.ai.context_generator import ContextGenerator

generator = ContextGenerator()

context = generator.generate("Diwali")

print("Context:", context)
print("Word count:", len(context.split()))