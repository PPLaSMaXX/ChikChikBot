import asyncio
import code
from distutils.cmd import Command
import html
import logging
import sys
import subprocess
import os
from os import environ, getenv

from aiogram import Bot, Dispatcher, Router, types
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.filters import Command
from aiogram.methods import SendMessage
from aiogram.types import Message, BotCommand
from aiogram.utils.formatting import Text, Code
from pyngrok import ngrok
from subprocess import Popen, PIPE, STDOUT
    
TOKEN = environ.get("TOKEN")

class IsRunning(Exception):
     def __init__(self, message):            
        super().__init__(message)


class NgrokClient:
    ssh_tunnel = None
    isRunning = False

    @staticmethod
    def getTunnelUrl():
        if NgrokClient.isRunning:
            return Text(NgrokClient.ssh_tunnel.data.get("public_url").strip("tcp://"))
        else:
            raise IsRunning("Tcp tunnel is not running!")

    @staticmethod
    def startTunnel():
        if not NgrokClient.isRunning:
            NgrokClient.ssh_tunnel = ngrok.connect("25565", "tcp")
            NgrokClient.isRunning = True
            return Text(
                "Successfully started! Running on url", NgrokClient.getTunnelUrl()
            )
        else:
            raise IsRunning(
                "Tcp tunneling is running! Check url by using ", Code("/ip"), " command"
            )

    @staticmethod
    def closeTunnel():
        if NgrokClient.isRunning:
            ngrok.disconnect(NgrokClient.ssh_tunnel.public_url)
            NgrokClient.isRunning = False
            return Text("Successfully closed the tcp tunneling!")
        else:
            raise IsRunning(
                "Tcp tunnel not started yet! Start by using ", Code("/startTunnel")
            )


class MinecraftServerClient:
    ServerClient = None
    isRunning = False

    @staticmethod
    def startServer():
        if not MinecraftServerClient.isRunning:
            MinecraftServerClient.ServerClient = subprocess.Popen(
                "java @user_jvm_args.txt @libraries/net/minecraftforge/forge/1.20.2-48.0.40/win_args.txt %*",
                shell=True,
                stdout=PIPE,
                stdin=PIPE,
                stderr=PIPE,
                cwd="C:/Home/minecraft server",
                universal_newlines=True,
                bufsize=0
            )
            MinecraftServerClient.isRunning = True
        else:
            raise IsRunning("Minecraft server is already running!")

    @staticmethod
    def stopServer():
        if MinecraftServerClient.isRunning:
            MinecraftServerClient.ServerClient.stdin.write("stop")
            MinecraftServerClient.isRunning = False
        else:
            raise IsRunning("Minecraft server is not running!")


dp = Dispatcher()


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    await message.answer(f"I am stupid. I am stupid...")


@dp.message(Command("ip"))
async def echo_ip(message: Message) -> None:
    try:
        await message.answer(**NgrokClient.getTunnelUrl().as_kwargs())
    except IsRunning as e:
        await message.answer(**Text(e).as_kwargs())


@dp.message(Command("startserver"))
async def startComplete(message: Message):
    try:
        MinecraftServerClient.startServer()
        
        await message.answer("Starting...")
        try:
            for stdout_line in iter(MinecraftServerClient.ServerClient.stdout.readline, ""):
                print(stdout_line)
                if(" Done " in stdout_line):
                    await message.answer("Server stated!")
                    break
        except Exception as e:
            message.answer(f"Error occured: {e}")
            print(e)
            
        await message.answer("Starting ngrokTunnel");    
        await message.answer(**NgrokClient.startTunnel().as_kwargs())
        await message.answer("All done. Have a great time!");
    
    except IsRunning as e:
        await message.answer(**Text(e).as_kwargs())       


@dp.message(Command("stopserver"))
async def stopComplete(message: Message):
    try:
        MinecraftServerClient.stopServer()        

        await message.answer("Stopping...")
            
        MinecraftServerClient.ServerClient.communicate()
        
        await message.answer("Server stopped");  
        await message.answer("Stopping ngrokTunnel");    
        await message.answer(**NgrokClient.closeTunnel().as_kwargs())
        await message.answer("All done. Seeyall!");
    
    except IsRunning as e:
        await message.answer(**Text(e).as_kwargs())  


async def main() -> None:
    bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML)
    
    await dp.start_polling(bot, skip_updates=True)
    

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
    

