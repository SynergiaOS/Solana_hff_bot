#!/usr/bin/env python3
"""
🛡️ EMERGENCY SECURE TRANSFER SCRIPT
Transfer 27.6 SOL from compromised wallet to secure cold storage
"""

import json
import os
import sys
from solana.rpc.api import Client
from solana.keypair import Keypair
from solana.transaction import Transaction
from solana.system_program import transfer, TransferParams
from solana.rpc.commitment import Confirmed

def emergency_transfer():
    """Execute emergency transfer of funds to secure wallet"""
    
    print("🚨 EMERGENCY SECURE TRANSFER PROTOCOL")
    print("=" * 50)
    
    # RPC connection
    rpc_url = "https://distinguished-blue-glade.solana-mainnet.quiknode.pro/a10fad0f63cdfe46533f1892ac720517b08fe580"
    client = Client(rpc_url, commitment=Confirmed)
    
    # Source wallet (compromised)
    source_wallet_file = "wallets/mainnet-trading-wallet.json"
    
    # Destination wallet (secure)
    dest_address = "5mEUmdxwFibJfvVrBVRjddufBKrLrpeTd4udqhgYpBGG"
    
    print(f"📂 Loading source wallet: {source_wallet_file}")
    
    # Load source wallet (handle ASCII format)
    try:
        with open(source_wallet_file, 'r') as f:
            wallet_data = json.load(f)
        
        # Convert ASCII array to proper format
        if isinstance(wallet_data, list) and len(wallet_data) > 64:
            # ASCII format - convert to string then to bytes
            key_string = ''.join([chr(b) for b in wallet_data])
            print(f"🔑 Detected ASCII format key")
            # This would need proper base58 decoding
            print("❌ ASCII format detected - manual conversion needed")
            return False
        else:
            # Proper format
            source_keypair = Keypair.from_secret_key(bytes(wallet_data))
            
    except Exception as e:
        print(f"❌ Error loading wallet: {e}")
        return False
    
    print(f"📍 Source address: {source_keypair.public_key}")
    print(f"📍 Destination address: {dest_address}")
    
    # Check source balance
    try:
        balance_response = client.get_balance(source_keypair.public_key)
        balance_lamports = balance_response['result']['value']
        balance_sol = balance_lamports / 1_000_000_000
        
        print(f"💰 Source balance: {balance_sol:.9f} SOL")
        
        if balance_sol < 0.001:
            print("❌ Insufficient balance for transfer")
            return False
            
    except Exception as e:
        print(f"❌ Error checking balance: {e}")
        return False
    
    # Calculate transfer amount (leave 0.01 SOL for fees)
    transfer_amount_sol = balance_sol - 0.01
    transfer_amount_lamports = int(transfer_amount_sol * 1_000_000_000)
    
    print(f"🔄 Transferring: {transfer_amount_sol:.9f} SOL")
    print(f"💸 Fee reserve: 0.01 SOL")
    
    # Confirm transfer
    confirm = input("\n⚠️  CONFIRM EMERGENCY TRANSFER? (type 'CONFIRM'): ")
    if confirm != 'CONFIRM':
        print("❌ Transfer cancelled")
        return False
    
    print("\n🚀 Executing emergency transfer...")
    
    # This is a template - actual implementation would need:
    # 1. Proper key format conversion
    # 2. Transaction building
    # 3. Signing and sending
    # 4. Confirmation waiting
    
    print("⚠️  MANUAL INTERVENTION REQUIRED:")
    print("1. Convert wallet format properly")
    print("2. Use Solana CLI for secure transfer:")
    print(f"   solana transfer {dest_address} {transfer_amount_sol} --from <proper_wallet_file>")
    
    return True

if __name__ == "__main__":
    emergency_transfer()
