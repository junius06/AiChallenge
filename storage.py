import openai

class TroubleshootingTraining:
    def __init__(self, chatgpt: ChatGPT):
        self.chatgpt = chatgpt
        self.current_issue = None
        self.current_solution = None

    async def start_training(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        # OpenAI Platform에서 문제를 가져옴
        response = openai.File.list()
        files = response['data']

        if files:
            # 랜덤 문제 선택
            selected_file = random.choice(files)
            file_content = openai.File.download(selected_file['id']).decode('utf-8')
            problem = json.loads(file_content)

            self.current_issue = problem["issue"]
            self.current_solution = problem["expected_solution"]

            # 문제 제시
            await update.message.reply_text(f"Task : {self.current_issue}\n\n문제를 해결하기 위한 방안을 제시하세요.")
        else:
            await update.message.reply_text("No issues found in OpenAI Platform Storage.")

    async def evaluate_solution(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user_solution = update.message.text
        prompt = f"Evaluate how close the following user-provided solution is to the expected solution: '{self.current_solution}'.\nUser solution: {user_solution}"
        
        # ChatGPT API를 통해 평가 요청
        evaluation = await self.chatgpt.request_chat_gpt(prompt)

        # 평가 결과 반환
        await update.message.reply_text(f"평가 결과: {evaluation}")
