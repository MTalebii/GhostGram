import asyncio
import aiohttp
from logger import logger

class DynamicPromptManager:
    def __init__(self):
        self.injectors = []
        self.register_injector(self.gold_dollar_injector)

    def register_injector(self, func):
        """Register an async injector function."""
        self.injectors.append(func)

    async def generate_dynamic_context(self, target_text: str) -> str:
        """
        Runs all registered injectors concurrently.
        Returns a formatted context string if any injectors return data.
        """
        if not target_text:
            return ""

        target_text_lower = str(target_text).lower()
        
        # Run all injectors concurrently
        tasks = [injector(target_text_lower) for injector in self.injectors]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        context_pieces = []
        for res in results:
            if isinstance(res, Exception):
                logger.error(f"⚠️ Dynamic Prompt Injector failed: {res}")
            elif res:
                context_pieces.append(res)
                
        if context_pieces:
            return "\n\n[DYNAMIC LIVE CONTEXT - ONLY VISIBLE TO AI]:\n" + "\n".join(context_pieces) + "\n"
        return ""

    async def gold_dollar_injector(self, target_text: str) -> str:
        """
        Injects the live Gold and Dollar (Tether) prices in Tomans if keywords are detected.
        """
        keywords = ['طلا', 'دلار', 'سکه', 'ارز', 'gold', 'dollar', 'tether', 'تتر']
        if not any(k in target_text for k in keywords):
            return ""

        try:
            logger.debug("[DYNAMIC_PROMPT] Keywords detected. Fetching live gold & dollar prices...")
            async with aiohttp.ClientSession() as session:
                # 1. Fetch Toman Rate (USDT to IRT from Nobitex)
                nobitex_url = "https://api.nobitex.ir/market/stats?srcCurrency=usdt&dstCurrency=irt"
                async with session.get(nobitex_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5) as res:
                    res.raise_for_status()
                    data = await res.json()
                    usd_to_toman = float(data["stats"]["usdt-irt"]["latest"])

                # 2. Fetch Global Gold (PAXG to USD from CoinGecko)
                gold_url = "https://api.coingecko.com/api/v3/simple/price?ids=pax-gold&vs_currencies=usd"
                async with session.get(gold_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5) as res:
                    res.raise_for_status()
                    data = await res.json()
                    xau_usd_price = float(data['pax-gold']['usd'])

                # 3. Calculate Final Price (18k Gold Gram in Tomans)
                price_per_gram_18k = (xau_usd_price / 31.1034) * 0.75
                final_toman = price_per_gram_18k * usd_to_toman

                return f"- Live Currency (Iran): 1 USD = {usd_to_toman:,.0f} Tomans\n- Live Gold (18k): 1 Gram = {final_toman:,.0f} Tomans"
        
        except Exception as e:
            logger.error(f"⚠️ Failed to fetch live gold/dollar prices: {e}")
            return ""

# Global singleton
dynamic_prompt_manager = DynamicPromptManager()
