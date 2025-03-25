import pickle
import skia
import asyncio
from nonebot import logger
from io import BytesIO
from nonebot import get_bot
from dynrender_skia.Core import DynRender
from nonebot.adapters.onebot.v11 import MessageSegment,Bot
from arielbot.plugins.Core.ariel_database import DataManager
from arielbot.plugins.Core.ariel_bili import Dynamic,Live


class PublicPusher:
    async def assign_tasks(self,task):
        await asyncio.gather(*[self.process_task(i,task["message"]) for i in task["target"]])
    
    async def process_task(self,push_target,message):
        bot:Bot = get_bot(str(push_target[1]))
        await bot.send_group_msg(group_id=push_target[0],message=message)


class DynPusher(PublicPusher):
    
    async def push_dynamic(self):
        follow_dynamic_list = await Dynamic().get_dynamic_from_follow_list()
        if follow_dynamic_list is None:
            return
        task_list = []
        async with DataManager() as m:
            for dynamic in follow_dynamic_list:
                result = await m.select_dyn_content(dynamic.message_id)
                if result:
                    continue
                logger.info(f"检测到{dynamic.header.name}的新动态: {dynamic.message_id}")
                all_push_group = await m.select_dynamic_push(dynamic.header.mid)
                await m.insert_dyn_data((dynamic.message_id,dynamic.header.name,pickle.dumps(dynamic)))
                if not all_push_group:
                    logger.info("没有需要推送的群，跳过该动态")
                    continue
                img = await DynRender().run(dynamic)
                img = skia.Image.fromarray(img, colorType=skia.ColorType.kRGBA_8888_ColorType)
                img_buffer = BytesIO()
                img.save(img_buffer)
                message = MessageSegment.text(f"{dynamic.header.name}发布了新动态:\n\n")+MessageSegment.text(f"传送门——>https://t.bilibili.com{dynamic.message_id}")+MessageSegment.image(img_buffer)
                task_list.append({"target":all_push_group,"message":message})
        if task_list:
            await asyncio.gather(*[self.assign_tasks(i) for i in task_list])
    
    
        
                
                
        
class LivePusher(PublicPusher):
    
    async def push_live(self):
        async with DataManager() as m:
            all_check_uid_list = await m.select_live_check_uid()
        if not all_check_uid_list:
            return
        all_live_stauts = {f"{i[0]}":i[1] for i in all_check_uid_list}
        all_check_uid_list = [i[0] for i in all_check_uid_list]
        check_result= await Live().get_room_info_by_uids(all_check_uid_list)
        if check_result  is None:
            return
        tasks = []
        for k,v in check_result.items():
            if v["live_status"] !=1:
                v["live_status"]=0
            
            if all_live_stauts[k] == v["live_status"]:
                continue
            if all_live_stauts[k] == 1:
                async with DataManager() as m:
                    await m.update_sub_target((v["uname"],0,v["uid"]))
                continue
            async with DataManager() as m:
                await m.update_sub_target((v["uname"],1,v["uid"]))
                all_push_target = await m.select_live_push(v["uid"])
            if not all_push_target:
                continue
            message = MessageSegment.text(f"【{v["uname"]}】开播啦!!!\n\n标题：{v["title"]}\n\n")+MessageSegment.text(f"传送门：https://live.bilibili.com{v["room_id"]}\n")+MessageSegment.image(v["cover_from_user"])
            tasks.append({"target":all_push_target,"message":message})
        if tasks:
            await asyncio.gather(*[self.assign_tasks(i) for i in tasks])
    
    
            
            
                
            
        
        
        
        
        

    
    