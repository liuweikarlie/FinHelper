class simple_qa:
    def __init__(self):
        self.config_list = [
            {
                'model': 'llama3-70b-8192',
                'api_key': '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',
                'base_url': "https://api.groq.com/openai/v1",
            }
        ]
        self.llm_config = {
            "config_list": self.config_list,
            "timeout": 120,
            "temperature": 0.0,
        }

        
