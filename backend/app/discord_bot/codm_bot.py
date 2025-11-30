"""
Discord bot for CODM match organization and community management
Handles match coordination, result verification, and community engagement
"""

import discord
from discord.ext import commands, tasks
import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import aiohttp
import os

logger = logging.getLogger(__name__)

class CODMDiscordBot(commands.Bot):
    """Discord bot for CODM match management"""
    
    def __init__(self, command_prefix='!', intents=None):
        if intents is None:
            intents = discord.Intents.default()
            intents.message_content = True
            intents.members = True
        
        super().__init__(command_prefix=command_prefix, intents=intents)
        self.backend_url = os.getenv("BACKEND_URL", "http://localhost:8001")
        self.api_token = os.getenv("DISCORD_BOT_TOKEN")
        
    async def on_ready(self):
        """Bot startup event"""
        print(f'{self.user} has connected to Discord!')
        print(f'Bot is in {len(self.guilds)} guilds')
        
        # Start background tasks
        self.update_match_status.start()
        self.cleanup_old_matches.start()
    
    async def on_message(self, message):
        """Handle incoming messages"""
        if message.author == self.user:
            return
        
        await self.process_commands(message)
    
    @commands.command(name='codm_help')
    async def codm_help(self, ctx):
        """Show CODM bot help"""
        embed = discord.Embed(
            title="🎮 CODM Match Bot Commands",
            description="Available commands for Call of Duty Mobile matches",
            color=0x00ff00
        )
        
        embed.add_field(
            name="Match Commands",
            value="`!create_match` - Create a new CODM match\n"
                  "`!join_match <match_id>` - Join an existing match\n"
                  "`!leave_match <match_id>` - Leave a match\n"
                  "`!match_status <match_id>` - Check match status",
            inline=False
        )
        
        embed.add_field(
            name="Result Commands",
            value="`!submit_result <match_id>` - Submit match result\n"
                  "`!my_matches` - View your matches\n"
                  "`!my_stats` - View your CODM statistics",
            inline=False
        )
        
        embed.add_field(
            name="Admin Commands",
            value="`!admin_pending` - View pending submissions\n"
                  "`!admin_approve <match_id>` - Approve submission\n"
                  "`!admin_reject <match_id> <reason>` - Reject submission",
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='create_match')
    async def create_match(self, ctx, game_mode: str, entry_fee: float):
        """Create a new CODM match"""
        try:
            # Validate game mode
            valid_modes = ["battle_royale", "multiplayer", "ranked"]
            if game_mode not in valid_modes:
                await ctx.send(f"❌ Invalid game mode. Valid modes: {', '.join(valid_modes)}")
                return
            
            # Validate entry fee
            if entry_fee < 50 or entry_fee > 50000:
                await ctx.send("❌ Entry fee must be between ₦50 and ₦50,000")
                return
            
            # Create match via API
            match_data = {
                "game_type": "call_of_duty",
                "match_type": game_mode,
                "entry_fee": entry_fee,
                "created_by": ctx.author.id,
                "discord_channel": ctx.channel.id
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.backend_url}/api/v1/matches",
                    json=match_data,
                    headers={"Authorization": f"Bearer {self.api_token}"}
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        match_id = result.get("task_id")
                        
                        embed = discord.Embed(
                            title="🎮 New CODM Match Created",
                            description=f"Match ID: `{match_id}`",
                            color=0x00ff00
                        )
                        embed.add_field(name="Game Mode", value=game_mode.title(), inline=True)
                        embed.add_field(name="Entry Fee", value=f"₦{entry_fee:,.2f}", inline=True)
                        embed.add_field(name="Created By", value=ctx.author.mention, inline=True)
                        embed.add_field(name="Status", value="🟡 Pending Players", inline=True)
                        
                        await ctx.send(embed=embed)
                    else:
                        await ctx.send("❌ Failed to create match. Please try again.")
        
        except Exception as e:
            logger.error(f"Error creating match: {str(e)}")
            await ctx.send("❌ An error occurred while creating the match.")
    
    @commands.command(name='join_match')
    async def join_match(self, ctx, match_id: str):
        """Join an existing CODM match"""
        try:
            # Join match via API
            join_data = {
                "match_id": match_id,
                "player_id": ctx.author.id,
                "discord_username": str(ctx.author)
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.backend_url}/api/v1/matches/{match_id}/join",
                    json=join_data,
                    headers={"Authorization": f"Bearer {self.api_token}"}
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        
                        embed = discord.Embed(
                            title="✅ Joined CODM Match",
                            description=f"Match ID: `{match_id}`",
                            color=0x00ff00
                        )
                        embed.add_field(name="Player", value=ctx.author.mention, inline=True)
                        embed.add_field(name="Status", value="🟢 Joined", inline=True)
                        
                        await ctx.send(embed=embed)
                    else:
                        error_data = await response.json()
                        await ctx.send(f"❌ Failed to join match: {error_data.get('detail', 'Unknown error')}")
        
        except Exception as e:
            logger.error(f"Error joining match: {str(e)}")
            await ctx.send("❌ An error occurred while joining the match.")
    
    @commands.command(name='submit_result')
    async def submit_result(self, ctx, match_id: str, kills: int, deaths: int, score: int):
        """Submit CODM match result"""
        try:
            # Validate input
            if kills < 0 or deaths < 0 or score < 0:
                await ctx.send("❌ Kills, deaths, and score must be non-negative numbers")
                return
            
            # Submit result via API
            result_data = {
                "match_id": match_id,
                "kills": kills,
                "deaths": deaths,
                "assists": 0,  # Default value
                "score": score,
                "game_mode": "multiplayer",  # Default value
                "submitted_by": ctx.author.id
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.backend_url}/api/v1/codm_matches/submit-result",
                    json=result_data,
                    headers={"Authorization": f"Bearer {self.api_token}"}
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        
                        embed = discord.Embed(
                            title="📊 CODM Result Submitted",
                            description=f"Match ID: `{match_id}`",
                            color=0x00ff00
                        )
                        embed.add_field(name="Kills", value=kills, inline=True)
                        embed.add_field(name="Deaths", value=deaths, inline=True)
                        embed.add_field(name="Score", value=score, inline=True)
                        embed.add_field(name="K/D Ratio", value=f"{kills/deaths:.2f}" if deaths > 0 else "∞", inline=True)
                        embed.add_field(name="Status", value="🟡 Pending Verification", inline=True)
                        
                        await ctx.send(embed=embed)
                    else:
                        error_data = await response.json()
                        await ctx.send(f"❌ Failed to submit result: {error_data.get('detail', 'Unknown error')}")
        
        except Exception as e:
            logger.error(f"Error submitting result: {str(e)}")
            await ctx.send("❌ An error occurred while submitting the result.")
    
    @commands.command(name='my_matches')
    async def my_matches(self, ctx):
        """View user's CODM matches"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.backend_url}/api/v1/codm_matches/submissions",
                    headers={"Authorization": f"Bearer {self.api_token}"}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        submissions = data.get("submissions", [])
                        
                        if not submissions:
                            await ctx.send("📭 You have no CODM matches yet.")
                            return
                        
                        embed = discord.Embed(
                            title="🎮 Your CODM Matches",
                            description=f"Total matches: {len(submissions)}",
                            color=0x0099ff
                        )
                        
                        for submission in submissions[:5]:  # Show last 5 matches
                            status_emoji = {
                                "pending": "🟡",
                                "approved": "✅",
                                "rejected": "❌",
                                "flagged": "🚩"
                            }.get(submission.get("status", "pending"), "❓")
                            
                            embed.add_field(
                                name=f"{status_emoji} Match {submission.get('id', 'N/A')}",
                                value=f"Kills: {submission.get('kills', 0)} | "
                                      f"Deaths: {submission.get('deaths', 0)} | "
                                      f"Score: {submission.get('score', 0)}",
                                inline=False
                            )
                        
                        await ctx.send(embed=embed)
                    else:
                        await ctx.send("❌ Failed to retrieve your matches.")
        
        except Exception as e:
            logger.error(f"Error getting user matches: {str(e)}")
            await ctx.send("❌ An error occurred while retrieving your matches.")
    
    @commands.command(name='my_stats')
    async def my_stats(self, ctx):
        """View user's CODM statistics"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.backend_url}/api/v1/codm_matches/stats",
                    headers={"Authorization": f"Bearer {self.api_token}"}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        stats = data.get("stats", {})
                        
                        embed = discord.Embed(
                            title="📊 Your CODM Statistics",
                            color=0x0099ff
                        )
                        
                        embed.add_field(name="Total Matches", value=stats.get("total_matches", 0), inline=True)
                        embed.add_field(name="Wins", value=stats.get("wins", 0), inline=True)
                        embed.add_field(name="Losses", value=stats.get("losses", 0), inline=True)
                        embed.add_field(name="Win Rate", value=f"{stats.get('win_rate', 0):.1f}%", inline=True)
                        embed.add_field(name="Total Kills", value=stats.get("total_kills", 0), inline=True)
                        embed.add_field(name="Total Deaths", value=stats.get("total_deaths", 0), inline=True)
                        embed.add_field(name="K/D Ratio", value=f"{stats.get('average_kd', 0):.2f}", inline=True)
                        embed.add_field(name="Best Kills", value=stats.get("best_kills", 0), inline=True)
                        embed.add_field(name="Total Earnings", value=f"₦{stats.get('total_earnings', 0):,.2f}", inline=True)
                        
                        await ctx.send(embed=embed)
                    else:
                        await ctx.send("❌ Failed to retrieve your statistics.")
        
        except Exception as e:
            logger.error(f"Error getting user stats: {str(e)}")
            await ctx.send("❌ An error occurred while retrieving your statistics.")
    
    @commands.command(name='admin_pending')
    @commands.has_role('Admin')  # Require Admin role
    async def admin_pending(self, ctx):
        """View pending CODM submissions (Admin only)"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.backend_url}/api/v1/codm_matches/admin/pending",
                    headers={"Authorization": f"Bearer {self.api_token}"}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        pending = data.get("pending_submissions", [])
                        
                        if not pending:
                            await ctx.send("✅ No pending CODM submissions.")
                            return
                        
                        embed = discord.Embed(
                            title="🚩 Pending CODM Submissions",
                            description=f"Total pending: {len(pending)}",
                            color=0xff9900
                        )
                        
                        for submission in pending[:5]:  # Show first 5
                            embed.add_field(
                                name=f"Match {submission.get('match_id', 'N/A')}",
                                value=f"Player: <@{submission.get('player_id', 'N/A')}>\n"
                                      f"Kills: {submission.get('kills', 0)} | "
                                      f"Deaths: {submission.get('deaths', 0)}\n"
                                      f"Score: {submission.get('score', 0)}",
                                inline=True
                            )
                        
                        await ctx.send(embed=embed)
                    else:
                        await ctx.send("❌ Failed to retrieve pending submissions.")
        
        except Exception as e:
            logger.error(f"Error getting pending submissions: {str(e)}")
            await ctx.send("❌ An error occurred while retrieving pending submissions.")
    
    @commands.command(name='admin_approve')
    @commands.has_role('Admin')  # Require Admin role
    async def admin_approve(self, ctx, match_id: str, *, admin_notes: str = ""):
        """Approve CODM submission (Admin only)"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.backend_url}/api/v1/codm_matches/admin/approve/{match_id}",
                    json={"admin_notes": admin_notes},
                    headers={"Authorization": f"Bearer {self.api_token}"}
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        
                        embed = discord.Embed(
                            title="✅ CODM Submission Approved",
                            description=f"Match ID: `{match_id}`",
                            color=0x00ff00
                        )
                        embed.add_field(name="Approved By", value=ctx.author.mention, inline=True)
                        embed.add_field(name="Notes", value=admin_notes or "No notes", inline=True)
                        embed.add_field(name="Processed At", value=result.get("processed_at", "N/A"), inline=True)
                        
                        await ctx.send(embed=embed)
                    else:
                        error_data = await response.json()
                        await ctx.send(f"❌ Failed to approve submission: {error_data.get('detail', 'Unknown error')}")
        
        except Exception as e:
            logger.error(f"Error approving submission: {str(e)}")
            await ctx.send("❌ An error occurred while approving the submission.")
    
    @commands.command(name='admin_reject')
    @commands.has_role('Admin')  # Require Admin role
    async def admin_reject(self, ctx, match_id: str, *, rejection_reason: str):
        """Reject CODM submission (Admin only)"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.backend_url}/api/v1/codm_matches/admin/reject/{match_id}",
                    json={"rejection_reason": rejection_reason},
                    headers={"Authorization": f"Bearer {self.api_token}"}
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        
                        embed = discord.Embed(
                            title="❌ CODM Submission Rejected",
                            description=f"Match ID: `{match_id}`",
                            color=0xff0000
                        )
                        embed.add_field(name="Rejected By", value=ctx.author.mention, inline=True)
                        embed.add_field(name="Reason", value=rejection_reason, inline=True)
                        embed.add_field(name="Processed At", value=result.get("processed_at", "N/A"), inline=True)
                        
                        await ctx.send(embed=embed)
                    else:
                        error_data = await response.json()
                        await ctx.send(f"❌ Failed to reject submission: {error_data.get('detail', 'Unknown error')}")
        
        except Exception as e:
            logger.error(f"Error rejecting submission: {str(e)}")
            await ctx.send("❌ An error occurred while rejecting the submission.")
    
    @tasks.loop(minutes=5)
    async def update_match_status(self):
        """Update match status every 5 minutes"""
        try:
            # This would check for match updates and notify channels
            logger.info("Updating match status...")
        except Exception as e:
            logger.error(f"Error updating match status: {str(e)}")
    
    @tasks.loop(hours=1)
    async def cleanup_old_matches(self):
        """Clean up old matches every hour"""
        try:
            # This would clean up old match data
            logger.info("Cleaning up old matches...")
        except Exception as e:
            logger.error(f"Error cleaning up old matches: {str(e)}")
    
    @update_match_status.before_loop
    async def before_update_match_status(self):
        """Wait until bot is ready before starting tasks"""
        await self.wait_until_ready()
    
    @cleanup_old_matches.before_loop
    async def before_cleanup_old_matches(self):
        """Wait until bot is ready before starting tasks"""
        await self.wait_until_ready()

def create_codm_bot():
    """Create and return CODM Discord bot instance"""
    return CODMDiscordBot()

async def run_codm_bot():
    """Run the CODM Discord bot"""
    bot = create_codm_bot()
    
    # Get Discord bot token from environment
    token = os.getenv("DISCORD_BOT_TOKEN")
    if not token:
        logger.error("DISCORD_BOT_TOKEN not found in environment variables")
        return
    
    try:
        await bot.start(token)
    except Exception as e:
        logger.error(f"Error running CODM bot: {str(e)}")

if __name__ == "__main__":
    # Run the bot
    asyncio.run(run_codm_bot())
