#!/usr/bin/env python3
"""
🔐 SECURE WALLET ACCESS UTILITY
Safely decrypt and use encrypted wallets for OVERMIND VAULT
"""

import os
import sys
import json
import subprocess
import tempfile
import getpass
from pathlib import Path
import hashlib
import time

class SecureWalletAccess:
    def __init__(self):
        self.vault_dir = Path.home() / ".overmind_vault"
        self.config_file = self.vault_dir / "wallet_config.json"
        self.temp_dir = None
        
    def load_config(self):
        """Load wallet configuration"""
        if not self.config_file.exists():
            raise Exception("❌ Vault not initialized. Run setup_secure_cold_storage.sh first")
        
        with open(self.config_file, 'r') as f:
            return json.load(f)
    
    def create_secure_temp_dir(self):
        """Create secure temporary directory"""
        self.temp_dir = tempfile.mkdtemp(prefix="overmind_vault_")
        os.chmod(self.temp_dir, 0o700)
        return self.temp_dir
    
    def cleanup_temp_dir(self):
        """Securely clean up temporary directory"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            # Shred all files in temp directory
            for file_path in Path(self.temp_dir).glob("*"):
                if file_path.is_file():
                    self.secure_delete(str(file_path))
            os.rmdir(self.temp_dir)
    
    def secure_delete(self, file_path):
        """Securely delete file by overwriting"""
        if not os.path.exists(file_path):
            return
        
        # Overwrite file multiple times
        file_size = os.path.getsize(file_path)
        with open(file_path, "r+b") as f:
            for _ in range(3):
                f.seek(0)
                f.write(os.urandom(file_size))
                f.flush()
                os.fsync(f.fileno())
        
        os.remove(file_path)
    
    def decrypt_wallet(self, wallet_name, password):
        """Decrypt wallet file"""
        config = self.load_config()
        
        if wallet_name not in config:
            raise Exception(f"❌ Wallet '{wallet_name}' not found")
        
        wallet_config = config[wallet_name]
        encrypted_file = wallet_config["encrypted_file"]
        
        if not os.path.exists(encrypted_file):
            raise Exception(f"❌ Encrypted wallet file not found: {encrypted_file}")
        
        # Create temporary file for decrypted wallet
        temp_dir = self.create_secure_temp_dir()
        temp_wallet = os.path.join(temp_dir, f"{wallet_name}.json")
        
        # Decrypt using OpenSSL
        cmd = [
            "openssl", "enc", "-aes-256-cbc", "-d",
            "-in", encrypted_file,
            "-out", temp_wallet,
            "-pass", f"pass:{password}"
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            print(f"✅ Wallet '{wallet_name}' decrypted successfully")
            return temp_wallet
        except subprocess.CalledProcessError as e:
            self.cleanup_temp_dir()
            raise Exception(f"❌ Decryption failed: {e.stderr}")
    
    def get_wallet_balance(self, wallet_address):
        """Get wallet balance from Solana network"""
        cmd = [
            "solana", "balance", wallet_address,
            "--url", "https://distinguished-blue-glade.solana-mainnet.quiknode.pro/a10fad0f63cdfe46533f1892ac720517b08fe580"
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            balance_str = result.stdout.strip()
            balance = float(balance_str.split()[0])
            return balance
        except Exception as e:
            print(f"⚠️ Could not get balance for {wallet_address}: {e}")
            return 0.0
    
    def transfer_funds(self, from_wallet_file, to_address, amount_sol, memo=""):
        """Transfer funds using decrypted wallet"""
        cmd = [
            "solana", "transfer", to_address, str(amount_sol),
            "--from", from_wallet_file,
            "--url", "https://distinguished-blue-glade.solana-mainnet.quiknode.pro/a10fad0f63cdfe46533f1892ac720517b08fe580",
            "--allow-unfunded-recipient"
        ]
        
        if memo:
            cmd.extend(["--with-memo", memo])
        
        print(f"🚀 Transferring {amount_sol} SOL to {to_address}")
        print("⚠️ Please confirm transaction details above")
        
        confirm = input("Type 'CONFIRM' to proceed: ")
        if confirm != 'CONFIRM':
            print("❌ Transfer cancelled")
            return None
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            print("✅ Transfer completed successfully")
            print(f"Transaction: {result.stdout.strip()}")
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            print(f"❌ Transfer failed: {e.stderr}")
            return None
    
    def emergency_transfer_to_cold_storage(self):
        """Emergency transfer of 27.6 SOL to cold storage"""
        print("🚨 EMERGENCY TRANSFER TO COLD STORAGE")
        print("=" * 50)
        
        config = self.load_config()
        cold_storage_address = config["cold_storage"]["address"]
        
        print(f"📍 Cold Storage Address: {cold_storage_address}")
        print("💰 Transferring 27.6 SOL from compromised wallet")
        
        # Get encryption password
        password = getpass.getpass("🔑 Enter encryption password: ")
        
        # For this emergency transfer, we need to manually handle the old wallet
        print("\n⚠️ MANUAL STEP REQUIRED:")
        print("1. Convert the old wallet format to proper JSON")
        print("2. Use solana CLI to transfer funds")
        print(f"3. Command: solana transfer {cold_storage_address} 27.0 --from OLD_WALLET_FILE")
        
        return cold_storage_address
    
    def setup_hot_wallets(self):
        """Setup hot wallets with small amounts for trading"""
        print("🔥 SETTING UP HOT WALLETS")
        print("=" * 30)
        
        config = self.load_config()
        password = getpass.getpass("🔑 Enter encryption password: ")
        
        # Decrypt cold storage wallet
        cold_wallet_file = self.decrypt_wallet("cold_storage", password)
        
        try:
            # Transfer to hot wallets
            transfers = [
                ("primary_trading", 1.0, "Primary trading capital"),
                ("hft_trading", 0.5, "HFT trading capital"),
                ("experimental", 0.1, "Experimental trading capital")
            ]
            
            for wallet_name, amount, memo in transfers:
                to_address = config[wallet_name]["address"]
                print(f"\n💸 Transferring {amount} SOL to {wallet_name}")
                self.transfer_funds(cold_wallet_file, to_address, amount, memo)
                time.sleep(2)  # Wait between transfers
            
        finally:
            # Always clean up decrypted files
            self.cleanup_temp_dir()
    
    def show_vault_status(self):
        """Show current vault status"""
        print("🏦 OVERMIND VAULT STATUS")
        print("=" * 25)
        
        config = self.load_config()
        total_balance = 0.0
        
        for wallet_name, wallet_config in config.items():
            address = wallet_config["address"]
            balance = self.get_wallet_balance(address)
            total_balance += balance
            
            print(f"{wallet_name:15} {address} {balance:8.6f} SOL")
        
        print("-" * 60)
        print(f"{'TOTAL':15} {'':<44} {total_balance:8.6f} SOL")
        print(f"\n💰 Total Vault Value: ~${total_balance * 155:.2f} USD")
    
    def interactive_menu(self):
        """Interactive menu for vault operations"""
        while True:
            print("\n🔐 OVERMIND VAULT - SECURE ACCESS")
            print("=" * 35)
            print("1. Show Vault Status")
            print("2. Emergency Transfer to Cold Storage")
            print("3. Setup Hot Wallets")
            print("4. Manual Transfer")
            print("5. Exit")
            
            choice = input("\nSelect option (1-5): ").strip()
            
            if choice == "1":
                self.show_vault_status()
            elif choice == "2":
                self.emergency_transfer_to_cold_storage()
            elif choice == "3":
                self.setup_hot_wallets()
            elif choice == "4":
                self.manual_transfer()
            elif choice == "5":
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid option")
    
    def manual_transfer(self):
        """Manual transfer between wallets"""
        print("💸 MANUAL TRANSFER")
        print("=" * 18)
        
        config = self.load_config()
        
        # Show available wallets
        print("Available wallets:")
        for i, wallet_name in enumerate(config.keys(), 1):
            address = config[wallet_name]["address"]
            balance = self.get_wallet_balance(address)
            print(f"{i}. {wallet_name} ({address}) - {balance:.6f} SOL")
        
        # Get transfer details
        from_wallet = input("\nFrom wallet name: ").strip()
        to_address = input("To address: ").strip()
        amount = float(input("Amount (SOL): ").strip())
        memo = input("Memo (optional): ").strip()
        
        if from_wallet not in config:
            print("❌ Invalid wallet name")
            return
        
        # Decrypt and transfer
        password = getpass.getpass("🔑 Enter encryption password: ")
        wallet_file = self.decrypt_wallet(from_wallet, password)
        
        try:
            self.transfer_funds(wallet_file, to_address, amount, memo)
        finally:
            self.cleanup_temp_dir()

def main():
    try:
        vault = SecureWalletAccess()
        vault.interactive_menu()
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
