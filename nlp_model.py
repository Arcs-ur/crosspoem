from transformers import BertTokenizer, BertModel
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

class BertSimilarityModel:
    def __init__(self):
        self.tokenizer = BertTokenizer.from_pretrained('bert-base-chinese')
        self.model = BertModel.from_pretrained('bert-base-chinese')
    
    def get_embedding(self, sentence):
        """获取句子的嵌入向量"""
        inputs = self.tokenizer(sentence, return_tensors='pt')
        outputs = self.model(**inputs)
        return outputs.last_hidden_state.mean(dim=1).detach().numpy()
    
    def calculate_similarity(self, user_input, correct_poem):
        """计算两个句子的相似度"""
        user_embedding = self.get_embedding(user_input)
        correct_embedding = self.get_embedding(correct_poem)
        similarity = cosine_similarity(user_embedding, correct_embedding)
        return similarity[0][0]