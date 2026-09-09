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
            logger.debug("[DYNAMIC_PROMPT] Keywords detected. Fetching live gold & dollar prices from Navasan GitHub...")
            async with aiohttp.ClientSession() as session:
                # 1. Fetch Currency (Fiat)
                fiat_url = "https://raw.githubusercontent.com/HosseinOdd/Navasan-API/main/data/fiat.json"
                async with session.get(fiat_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5) as res:
                    res.raise_for_status()
                    fiat_data = await res.json(content_type=None)
                    usd_to_toman = float(fiat_data.get("usd", {}).get("value", 0))

                # 2. Fetch Gold
                gold_url = "https://raw.githubusercontent.com/HosseinOdd/Navasan-API/main/data/gold.json"
                async with session.get(gold_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5) as res:
                    res.raise_for_status()
                    gold_data = await res.json(content_type=None)
                    price_per_gram_18k = float(gold_data.get("18ayar", {}).get("value", 0))
                    sekkeh = float(gold_data.get("sekkeh", {}).get("value", 0))

                pieces = []
                if usd_to_toman > 0:
                    pieces.append(f"- Live Currency (Iran): 1 USD = {usd_to_toman:,.0f} Tomans")
                if price_per_gram_18k > 0:
                    pieces.append(f"- Live Gold (18k): 1 Gram = {price_per_gram_18k:,.0f} Tomans")
                if sekkeh > 0:
                    pieces.append(f"- Live Coin (Emami): 1 Coin = {sekkeh:,.0f} Tomans")
                    
                return "\n".join(pieces)
        
        except Exception as e:
            logger.error(f"⚠️ Failed to fetch live gold/dollar prices: {e}")
            return ""

# Global singleton
dynamic_prompt_manager = DynamicPromptManager()
