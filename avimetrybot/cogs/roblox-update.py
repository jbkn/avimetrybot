import requests
import discord
from discord.ext import commands, tasks
import random
import time
import asyncio
import os
from dotenv import load_dotenv
from datetime import date

class RobloxUpdate(commands.Cog):
    def __init__(self, avimetry):
        self.avimetry=avimetry

    async def my_loop(self):
        while True:
            a = requests.get('http://setup.roblox.com/version')
            await asyncio.sleep(10)
            b = requests.get('http://setup.roblox.com/version')
            if b.text not in a.text:
                print("Update Detected!")
                channel = discord.utils.get(self.avimetry.get_all_channels(),  name='gaming-announcements')
                embed = discord.Embed(title="<:roblox:788835896354013229> A ROBLOX update has been detected.", description= "If you don't want ROBLOX to update, keep ROBLOX open. Please wait while people update their cool lego hak.")
                embed.add_field(name="Latest Version", value=f"{b.text}", inline=True)
                embed.add_field(name="Last Version", value=f"{a.text}", inline=True)
                embed.set_footer(text="If you want to get pinged when ROBLOX updates, use the command 'a.updateping'.")
                await channel.send('<@&783946910364073985>', embed=embed)

#Roblox Version Command
    @commands.command(aliases=['rblxver', 'rversion'], brief="Gets the current ROBLOX version.")
    async def robloxversion(self, ctx):
        a = requests.get('http://setup.roblox.com/version')
        rverembed = discord.Embed()
        rverembed.add_field(name='<:roblox:788835896354013229> Current Version', value="``"+a.text+"``", inline=True)
        await ctx.channel.send(embed=rverembed)
    
    @commands.command(brief="Get pinged if you want to know when a ROBLOX update arrives.")
    async def updateping(self, ctx):
        member = ctx.author
        role = discord.utils.get(member.guild.roles, name="RobloxUpdate")
        if role in member.roles:
            await discord.Member.remove_roles(member, role)
            ra=discord.Embed()
            ra.add_field(name="<:roblox:788835896354013229> Roblox Update Ping", value="You will no longer get pinged when ROBLOX recieves an update.")
            await ctx.send(embed=ra)
        else:
            await discord.Member.add_roles(member, role)
            ru=discord.Embed()
            ru.add_field(name="<:roblox:788835896354013229> Roblox Update Ping", value="You will now get pinged everytime ROBLOX recieves an update.")
            await ctx.send(embed=ru)

    @commands.Cog.listener()
    async def on_ready(self):
        self.avimetry.loop.create_task(self.my_loop())
def setup(avimetry):
    avimetry.add_cog(RobloxUpdate(avimetry))