
import qrcode
import time
import pickle
from io import BytesIO
from nonebot import logger
from ariel_bili import Login,UserInfo
from ariel_database import DataManager
from urllib.parse import urlsplit, parse_qs
from nonebot.adapters.onebot.v11 import Bot
from nonebot.adapters.onebot.v11 import MessageSegment,GroupMessageEvent


class LoginTools:
    
    async def login_handle(self,bot:Bot,event:GroupMessageEvent):
        login = Login()
        scan_url =  await login.get_qrcode_key
        if scan_url is None:
            await bot.send(event=event,message=MessageSegment.text("获取扫码链接失败"))
            return
        qrcode_buffer = BytesIO()
        qr = qrcode.QRCode()
        qr.add_data(scan_url)
        img = qr.make_image(image_factory=qrcode.image.pure.PyPNGImage)
        img.save(qrcode_buffer)
        await bot.send(event,message=MessageSegment.image(qrcode_buffer))
        while True:
            scan_result = await login.check_scan_result()
            if scan_result is None or scan_result["code"]==86038:
                await bot.send(event,"登陆失败")
                break
            if scan_result["code"] == 0:
                cookies = await self.__parse_cookie(scan_result)
                if cookies is None:
                    await bot.send(event,MessageSegment.text("cookie 解析失败"))
                    break
                async with DataManager() as d:
                    await d.insert_cookie((pickle.dumps(cookies),scan_result["refresh_token"]))
                break
            time.sleep(3)

    
    async def __parse_cookie(self,data):
        try:
            query_str = urlsplit(data["url"]).query
            params = parse_qs(query_str)
            cookies = {k: v[0] for k, v in params.items()}
            cookies.pop("gourl")
            return cookies
        except Exception as e:
            logger.error(e)
            return None

class PublicSubTools:
    def __init__(self,uid):
        self.uid = uid
    
    async def check_uid_info(self):
        uinfo = UserInfo()
        data = await uinfo.get_user_info_by_uid(self.uid)
        return data
    
    async def check_uid_in_group(self,bot:int,groupId:int):
        async with DataManager() as m:
            return await m.select_sub_chennal((self.uid,bot,groupId))
    
    async def check_uid_has_sub(self):
        async with DataManager() as m:
            return await m.select_sub_target(self.uid)
    
    async def follow_user(self,uid,act):
        uinfo = UserInfo()
        return await uinfo.change_follow_status(uid,act)
        

    
class AddSubTools(PublicSubTools):
    def __init__(self, uid):
        super().__init__(uid)
        
    async def add_sub_processor(self,event:GroupMessageEvent):
        check_sub_result = await self.check_uid_has_sub()
        if check_sub_result:
            check_uid_in_group_result = await self.check_uid_in_group(event.self_id,event.group_id)
            if check_uid_in_group_result:
                if check_uid_in_group_result[0]==0 or check_uid_in_group_result[1]==0:
                    async with DataManager() as m:
                        await m.update_sub_chennal((1,1,self.uid,event.group_id,event.self_id))
                    return f"成功添加订阅 --> {check_sub_result[0]}({self.uid})"
                else:
                    return f"本群已订阅过 --> {check_sub_result[0]}({self.uid})"
            else:
                async with DataManager() as m:
                    await m.insert_sub_chennal((self.uid,event.group_id,event.self_id))
                return "成功添加订阅 --> {check_sub_result[0]}({self.uid})"
        else:
            uid_info = await self.check_uid_info()
            if isinstance(uid_info,str):
                return uid_info
            if uid_info["following"] != "true":
                follow_result =  await self.follow_user(self.uid,1)
                if not follow_result:
                    return "添加订阅失败"
            async with DataManager() as m:
                await m.insert_sub_target((self.uid,uid_info["card"]["name"],0))
                await m.insert_sub_chennal((self.uid,event.group_id,event.self_id))
            return f"成功添加订阅 --> {uid_info["card"]["name"]}({self.uid})"            

class DelSubTools(PublicSubTools):
    def __init__(self, uid):
        super().__init__(uid)
    
    
    async def del_sub_processor(self,event:GroupMessageEvent):
        check_uid_in_group_result = await self.check_uid_in_group(event.self_id,event.group_id)
        if not check_uid_in_group_result:
            return f"本群没有订阅 --> {self.uid}"
        else:
            async with DataManager() as m:
                await m.update_sub_chennal((0,0,self.uid,event.group_id,event.self_id))
                uid_info = await m.select_sub_target(self.uid)
            return f"成功删除订阅 --> {uid_info[0]}({self.uid})"

class UpdataSubTools(PublicSubTools):
    def __init__(self, uid):
        super().__init__(uid)
        
    async def update_sub_handler(self,event:GroupMessageEvent,live_active:int=None, dyn_active:int = None):
        check_uid_in_group_result = await self.check_uid_in_group(event.self_id,event.group_id)
        if not check_uid_in_group_result:
            return f"本群没有订阅 --> {self.uid}"
        old_live_active = check_uid_in_group_result[0]
        old_dyn_active = check_uid_in_group_result[1]
        async with DataManager() as m:
            if live_active is None:
                await m.update_sub_chennal((old_live_active,dyn_active,self.uid,event.group_id,event.self_id))
                return "开启动态推送成功" if dyn_active==1 else "关闭动态推送成功"
            else:
                await m.update_sub_chennal((live_active,old_dyn_active,self.uid,event.group_id,event.self_id))
                return "开启直播推送成功" if live_active==1 else "关闭直播推送成功"
                
            
         