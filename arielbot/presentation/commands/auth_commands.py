def make_login_handler(auth_service):
    async def handler(bot, event):
        await auth_service.login(bot, event)
    return handler