from io import BytesIO
import requests
import plugins
from plugins import *
from bridge.context import ContextType
from bridge.reply import Reply, ReplyType
from common.log import logger
from urllib.parse import quote

@plugins.register(name="qr",
                  desc="转二维码",
                  version="1.0",
                  author="masterke",
                  desire_priority=100)
class qr(Plugin):
    content: str = None
    # config_data = None
    def __init__(self):
        super().__init__()
        self.handlers[Event.ON_HANDLE_CONTEXT] = self.on_handle_context
        logger.info(f"[{__class__.__name__}] inited")

    def get_help_text(self, **kwargs):
        help_text = f"发送【二维码 （需要转二维码的内容）】"
        return help_text

    def on_handle_context(self, e_context: EventContext):
        # 只处理文本消息
        if e_context['context'].type != ContextType.TEXT:
            return
        self.content = e_context["context"].content.strip()
        
        if self.content.startswith("二维码"):
            logger.info(f"[{__class__.__name__}] 收到消息: {self.content}")
            # # 读取配置文件
            # config_path = os.path.join(os.path.dirname(__file__),"config.json")
            # if os.path.exists(config_path):
            #     with open(config_path, 'r') as file:
            #         self.config_data = json.load(file)
            # else:
            #     logger.error(f"请先配置{config_path}文件")
            #     return
            
            reply = Reply()
            result = self.qr()
            if result != None:
                reply.type = ReplyType.IMAGE
                reply.content = result
                e_context["reply"] = reply
                e_context.action = EventAction.BREAK_PASS
            else:
                reply.type = ReplyType.ERROR
                reply.content = "获取失败,等待修复⌛️"
                e_context["reply"] = reply
                e_context.action = EventAction.BREAK_PASS

    def qr(self):
        if self.content.startswith("二维码 "):
            self.content = self.content[4:]
        elif self.content.startswith("二维码"):
            self.content = self.content[3:]
        logger.info(f"[{__class__.__name__}] 转换内容为：{self.content}")
        self.content = quote(self.content)
        try:
            #主接口
            url = "https://api.qqsuu.cn/api/dm-qrcode"
            params = f"frame=1&e=L&text={self.content}&size=100"
            headers = {'Content-Type': "application/x-www-form-urlencoded"}
            response = requests.get(url=url,
                                        params=params,
                                        headers=headers,
                                        timeout=2)
            if response.status_code == 200:
                logger.info(f"主接口获取成功,返回的数据前10字节为：{response.content[:10]}")
                image_bytes = response.content
                # 使用BytesIO保存到内存中
                image_in_memory = BytesIO(image_bytes)
                return image_in_memory
            else:
                logger.error(f"主接口请求失败:{response.status_code}")
                raise requests.ConnectionError
        except Exception as e:
            logger.error(f"主接口抛出异常:{e}")
            try:
                #备用接口
                url = f"https://ai.vvhan.com/api/qr"
                params = f"text={self.content}"
                headers = {'Content-Type': "application/x-www-form-urlencoded"}
                response = requests.get(url=url,
                                        params=params,
                                        headers=headers,
                                        timeout=4)
                if response.status_code == 200:
                    logger.info(f"备用接口获取成功,返回的数据前10字节为：{response.content[:10]}")
                    image_bytes = response.content
                    # 使用BytesIO保存到内存中
                    image_in_memory = BytesIO(image_bytes)
                    return image_in_memory
                else:
                    logger.error(f"备用接口请求失败:{response.status_code}")
            except Exception as e:
                logger.error(f"备用接口抛出异常:{e}")

        logger.error(f"所有接口都挂了,无法获取")
        return None
