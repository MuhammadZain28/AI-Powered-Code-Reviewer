from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")

# Save locally
model.save("./models/all-MiniLM-L6-v2")