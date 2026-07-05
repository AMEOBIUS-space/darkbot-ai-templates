#!/usr/bin/env python3
"""Demo for Solidity Template — shows contract structure, deployment, presale."""
import json

def demo():
    print("=" * 50)
    print("⛓ DarkBot AI — Solidity ERC20+Presale Demo")
    print("=" * 50)
    print()
    
    print("📋 Contract: DarkBotToken (DBAI)")
    print("  Type: ERC20 + Ownable (OpenZeppelin)")
    print("  Max Supply: 1,000,000 DBAI")
    print("  Presale Price: 0.001 ETH per DBAI")
    print("  Presale Active: true")
    print()
    
    # Simulate deployment
    print("🚀 Deploying to Ethereum Sepolia...")
    print("  → Contract address: 0xabc123...def456")
    print("  → Gas used: 2,450,000")
    print("  → TX: 0xabc789...")
    print()
    
    # Simulate whitelist
    print("✅ addToWhitelist([0xuser1, 0xuser2, 0xuser3])")
    print("  → 3 addresses whitelisted")
    print()
    
    # Simulate presale purchase
    buy_amount = 0.1  # ETH
    tokens = int(buy_amount / 0.001)
    print(f"💰 buyPresale() with {buy_amount} ETH")
    print(f"  → Tokens received: {tokens} DBAI")
    print(f"  → Event: PresalePurchase(buyer=0xuser1, amount={tokens}, cost={buy_amount} ETH)")
    print()
    
    # Simulate withdraw
    print("🏦 withdrawETH() by owner")
    print(f"  → Withdrawn: {buy_amount} ETH to owner")
    print()
    
    print("✅ Contract features:")
    print("  • ERC20 (transfer, balanceOf, approve)")
    print("  • Whitelist presale mechanism")
    print("  • Owner withdrawal")
    print("  • Event logging")
    print("  • Foundry tests + deploy script")
    print()
    print("Buy template: @darkbot_ai_bot | $69 | BTC/USDT/ETH/XMR")
    print("=" * 50)

if __name__ == "__main__":
    demo()
