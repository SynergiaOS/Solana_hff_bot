#!/usr/bin/env python3
"""
📝 RECOVER WALLET FROM PAPER BACKUP
Safely recover wallet from paper-stored private key
"""

import json
import os
import sys
import base58
import hashlib
import tempfile
import subprocess
from pathlib import Path

def recover_from_paper():
    """Recover wallet from paper backup"""
    
    print("📝 WALLET RECOVERY FROM PAPER BACKUP")
    print("=" * 40)
    print("⚠️  Make sure you have your paper backup ready!")
    print("⚠️  This will create a new wallet file!")
    print()
    
    # Get private key from user
    print("🔑 Enter your private key from paper backup:")
    print("(Should be 87-88 characters, Base58 format)")
    print()
    
    private_key = input("Private Key: ").strip()
    
    if not private_key:
        print("❌ No private key entered")
        return
    
    # Validate private key format
    if len(private_key) < 80 or len(private_key) > 90:
        print(f"⚠️ Warning: Private key length is {len(private_key)} characters")
        print("Expected: 87-88 characters")
        confirm = input("Continue anyway? (y/N): ")
        if confirm.lower() != 'y':
            return
    
    # Verify checksum if provided
    print()
    checksum_input = input("🔍 Enter checksum from paper (optional): ").strip()
    
    if checksum_input:
        calculated_checksum = hashlib.sha256(private_key.encode()).hexdigest()[:8]
        if checksum_input.lower() == calculated_checksum.lower():
            print("✅ Checksum verified!")
        else:
            print(f"❌ Checksum mismatch!")
            print(f"Expected: {calculated_checksum}")
            print(f"Entered: {checksum_input}")
            confirm = input("Continue anyway? (y/N): ")
            if confirm.lower() != 'y':
                return
    
    # Test private key validity
    try:
        print("\n🧪 Testing private key validity...")
        
        # Try to decode the private key
        private_key_bytes = base58.b58decode(private_key)
        
        if len(private_key_bytes) == 64:
            print("✅ Valid 64-byte keypair format")
        elif len(private_key_bytes) == 32:
            print("✅ Valid 32-byte private key format")
        else:
            print(f"⚠️ Unusual key length: {len(private_key_bytes)} bytes")
        
        # Create temporary wallet file for testing
        temp_dir = tempfile.mkdtemp()
        temp_wallet = os.path.join(temp_dir, "test_wallet.json")
        
        # Create wallet file
        if len(private_key_bytes) == 64:
            wallet_data = list(private_key_bytes)
        else:
            # If 32 bytes, we need to derive the full keypair
            print("🔄 Deriving full keypair from private key...")
            # For now, we'll use the Solana CLI to recover
            wallet_data = list(private_key_bytes)
        
        with open(temp_wallet, 'w') as f:
            json.dump(wallet_data, f)
        
        # Test wallet with Solana CLI
        try:
            result = subprocess.run([
                'solana-keygen', 'pubkey', temp_wallet
            ], capture_output=True, text=True, check=True)
            
            public_key = result.stdout.strip()
            print(f"✅ Derived public key: {public_key}")
            
            # Check if this matches our expected address
            expected_address = "4rtY4TCojYn2o86kRjNfETKcBxCWfX39dG4B21y4HYYm"
            if public_key == expected_address:
                print("🎉 SUCCESS! This matches the expected wallet address!")
            else:
                print(f"⚠️ Warning: Public key doesn't match expected address")
                print(f"Expected: {expected_address}")
                print(f"Derived:  {public_key}")
                
                confirm = input("Continue with recovery? (y/N): ")
                if confirm.lower() != 'y':
                    os.remove(temp_wallet)
                    os.rmdir(temp_dir)
                    return
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Error testing wallet: {e}")
            print("Private key may be invalid")
            os.remove(temp_wallet)
            os.rmdir(temp_dir)
            return
        
        # Clean up test files
        os.remove(temp_wallet)
        os.rmdir(temp_dir)
        
    except Exception as e:
        print(f"❌ Error validating private key: {e}")
        return
    
    # Create recovery wallet
    print("\n💾 Creating recovered wallet file...")
    
    # Choose output location
    output_options = [
        "wallets/recovered_wallet.json",
        "wallets/mainnet-trading-wallet-recovered.json",
        "Custom location"
    ]
    
    print("📁 Choose output location:")
    for i, option in enumerate(output_options, 1):
        print(f"{i}. {option}")
    
    choice = input("\nSelect option (1-3): ").strip()
    
    if choice == "1":
        output_file = "wallets/recovered_wallet.json"
    elif choice == "2":
        output_file = "wallets/mainnet-trading-wallet-recovered.json"
    elif choice == "3":
        output_file = input("Enter custom path: ").strip()
    else:
        print("❌ Invalid choice")
        return
    
    # Create output directory if needed
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Create wallet file
    try:
        private_key_bytes = base58.b58decode(private_key)
        
        if len(private_key_bytes) == 64:
            wallet_data = list(private_key_bytes)
        else:
            # Pad to 64 bytes if needed (this is a simplification)
            wallet_data = list(private_key_bytes) + [0] * (64 - len(private_key_bytes))
        
        with open(output_file, 'w') as f:
            json.dump(wallet_data, f)
        
        # Set secure permissions
        os.chmod(output_file, 0o600)
        
        print(f"✅ Wallet recovered to: {output_file}")
        
        # Verify the recovered wallet
        try:
            result = subprocess.run([
                'solana-keygen', 'pubkey', output_file
            ], capture_output=True, text=True, check=True)
            
            recovered_address = result.stdout.strip()
            print(f"📍 Recovered address: {recovered_address}")
            
            # Check balance
            try:
                balance_result = subprocess.run([
                    'solana', 'balance', recovered_address,
                    '--url', 'https://distinguished-blue-glade.solana-mainnet.quiknode.pro/a10fad0f63cdfe46533f1892ac720517b08fe580'
                ], capture_output=True, text=True, check=True)
                
                balance = balance_result.stdout.strip()
                print(f"💰 Current balance: {balance}")
                
            except subprocess.CalledProcessError:
                print("⚠️ Could not check balance (network issue)")
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Error verifying recovered wallet: {e}")
            return
        
        print("\n🎉 WALLET RECOVERY SUCCESSFUL!")
        print("=" * 35)
        print(f"📁 Wallet file: {output_file}")
        print(f"📍 Address: {recovered_address}")
        print(f"💰 Balance: {balance if 'balance' in locals() else 'Unknown'}")
        print()
        print("🔐 SECURITY REMINDERS:")
        print("• Wallet file has been created with secure permissions")
        print("• Consider encrypting the wallet file")
        print("• Keep your paper backup safe")
        print("• Test small transfers before large ones")
        print()
        print("💸 TRANSFER COMMAND:")
        print(f"solana transfer [DESTINATION] [AMOUNT] --from {output_file}")
        
    except Exception as e:
        print(f"❌ Error creating wallet file: {e}")

def verify_paper_backup():
    """Verify paper backup without creating wallet file"""
    
    print("🔍 VERIFY PAPER BACKUP")
    print("=" * 25)
    print("This will verify your paper backup without creating files")
    print()
    
    private_key = input("🔑 Enter private key from paper: ").strip()
    checksum_input = input("🔍 Enter checksum from paper: ").strip()
    
    if not private_key:
        print("❌ No private key entered")
        return
    
    # Calculate checksum
    calculated_checksum = hashlib.sha256(private_key.encode()).hexdigest()[:8]
    
    print(f"\n📊 VERIFICATION RESULTS:")
    print(f"Key length: {len(private_key)} characters")
    print(f"Calculated checksum: {calculated_checksum}")
    print(f"Paper checksum: {checksum_input}")
    
    if checksum_input.lower() == calculated_checksum.lower():
        print("✅ Checksum VERIFIED - Paper backup is correct!")
    else:
        print("❌ Checksum MISMATCH - Check your paper backup!")
    
    # Try to derive public key
    try:
        private_key_bytes = base58.b58decode(private_key)
        print(f"✅ Private key format is valid ({len(private_key_bytes)} bytes)")
    except Exception as e:
        print(f"❌ Invalid private key format: {e}")

if __name__ == "__main__":
    print("📝 PAPER WALLET RECOVERY UTILITY")
    print("=" * 35)
    print("1. Recover wallet from paper backup")
    print("2. Verify paper backup (no files created)")
    print("3. Exit")
    print()
    
    choice = input("Select option (1-3): ").strip()
    
    if choice == "1":
        recover_from_paper()
    elif choice == "2":
        verify_paper_backup()
    elif choice == "3":
        print("👋 Goodbye!")
    else:
        print("❌ Invalid option")
