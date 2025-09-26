import google.generativeai as genai
import google.generativeai.protos as protos
import json
from db_handler import search_book, create_order

class BookStoreChatbotGemini:
    def __init__(self, api_key):
        genai.configure(api_key=api_key)
        
        # Định nghĩa tools với schema chuẩn
        self.tools = [
            genai.protos.Tool(
                function_declarations=[
                    genai.protos.FunctionDeclaration(
                        name="search_book",
                        description="Tìm kiếm và tra cứu thông tin sách trong cửa hàng dựa trên tên sách hoặc tác giả. Ví dụ: 'Tìm sách Đắc Nhân Tâm' hoặc 'Tìm sách của Tô Hoài'.",
                        parameters=genai.protos.Schema(
                            type=genai.protos.Type.OBJECT,
                            properties={
                                "title": genai.protos.Schema(
                                    type=genai.protos.Type.STRING,
                                    description="Tên cuốn sách, ví dụ: Đắc Nhân Tâm"
                                ),
                                "author": genai.protos.Schema(
                                    type=genai.protos.Type.STRING,
                                    description="Tên tác giả, ví dụ: Dale Carnegie"
                                )
                            }
                        ),
                    ),
                    genai.protos.FunctionDeclaration(
                        name="create_order",
                        description="Tạo đơn hàng mới khi người dùng cung cấp đầy đủ thông tin: tên khách hàng, số điện thoại, địa chỉ, tên sách và số lượng. Ví dụ: 'Mua 1 cuốn Nhà Giả Kim, tên A, sdt 0123456789, địa chỉ Hà Nội'.",
                        parameters=genai.protos.Schema(
                            type=genai.protos.Type.OBJECT,
                            properties={
                                "customer_name": genai.protos.Schema(
                                    type=genai.protos.Type.STRING,
                                    description="Tên của khách hàng"
                                ),
                                "phone": genai.protos.Schema(
                                    type=genai.protos.Type.STRING,
                                    description="Số điện thoại của khách hàng"
                                ),
                                "address": genai.protos.Schema(
                                    type=genai.protos.Type.STRING,
                                    description="Địa chỉ giao hàng"
                                ),
                                "book_title": genai.protos.Schema(
                                    type=genai.protos.Type.STRING,
                                    description="Tên cuốn sách khách muốn mua"
                                ),
                                "quantity": genai.protos.Schema(
                                    type=genai.protos.Type.INTEGER,
                                    description="Số lượng sách khách muốn mua, phải là số nguyên dương"
                                )
                            },
                            required=["customer_name", "phone", "address", "book_title", "quantity"]
                        ),
                    )
                ]
            )
        ]

        # Debug: In schema để kiểm tra
        for tool in self.tools:
            for func in tool.function_declarations:
                print(f"Function: {func.name}, Parameters: {func.parameters}")

        # Khởi tạo model
        self.model = genai.GenerativeModel(
            model_name="gemini-2.0-flash-lite-001",
            tools=self.tools,
            generation_config={"temperature": 0.7}
        )

        self.available_functions = {
            "search_book": search_book,
            "create_order": create_order,
        }

    def get_response(self, history):
        try:
            # Kiểm tra format history
            if not all(isinstance(msg, dict) and "role" in msg and "parts" in msg for msg in history):
                return "Lịch sử trò chuyện không đúng định dạng. Vui lòng thử lại."

            # Giới hạn history (10 message cuối)
            history = history[-10:]

            # Debug: In history để kiểm tra
            print(f"History: {json.dumps(history, indent=2, ensure_ascii=False)}")

            # Kiểm tra nếu history rỗng hoặc không có message người dùng
            if not history or not any(msg["role"] == "user" for msg in history):
                return "Vui lòng nhập yêu cầu để tôi xử lý."

            # Lấy message người dùng mới nhất
            last_user_message = next((msg["parts"][0] for msg in reversed(history) if msg["role"] == "user"), None)
            if not last_user_message:
                return "Không tìm thấy input người dùng. Vui lòng thử lại."

            # Bắt đầu chat session
            chat = self.model.start_chat(history=history)
            
            # Gửi message mới nhất
            response = chat.send_message(last_user_message, stream=False)
            
            # Xử lý function calls
            for part in response.parts:
                if hasattr(part, 'function_call') and part.function_call:
                    function_name = part.function_call.name
                    function_args = {k: v for k, v in part.function_call.args.items()}
                    
                    # Ép kiểu quantity thành integer cho create_order
                    if function_name == "create_order" and "quantity" in function_args:
                        try:
                            function_args["quantity"] = int(function_args["quantity"])
                            if function_args["quantity"] <= 0:
                                return "Số lượng phải là số nguyên dương."
                        except ValueError:
                            return "Số lượng không hợp lệ. Vui lòng nhập số nguyên dương."
                    
                    print(f"Calling function: {function_name} with args: {function_args}")
                    
                    function_to_call = self.available_functions[function_name]
                    function_response_content = function_to_call(**function_args)
                    
                    # Debug: In function response
                    print(f"Function response: {function_response_content}")
                    
                    # Gửi function response lại cho model
                    function_response = {
                        "parts": [{
                            "function_response": {
                                "name": function_name,
                                "response": {"result": function_response_content}
                            }
                        }]
                    }
                    print(f"Function response sent: {json.dumps(function_response, indent=2, ensure_ascii=False)}")
                    response = chat.send_message(function_response)
            
            return response.text
        except Exception as e:
            print(f"Error in get_response: {str(e)}")
            if "API" in str(e):
                return "Lỗi kết nối với API. Vui lòng thử lại sau."
            elif "database" in str(e).lower():
                return "Lỗi truy cập cơ sở dữ liệu. Vui lòng thử lại."
            return f"Xin lỗi, đã có lỗi xảy ra: {str(e)}. Vui lòng thử lại."