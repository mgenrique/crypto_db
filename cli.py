# cli.py
#!/usr/bin/env python3

import requests
import json
import os
import sys
import time
from typing import Optional, Dict, Any
from datetime import datetime
from pathlib import Path

class CryptoDashboardCLI:
    """CLI Menu-driven para interactuar con FastAPI Crypto Dashboard"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.token: Optional[str] = None
        self.user: Optional[Dict] = None
        self.config_file = Path("cli_config.json")
        self.load_config()
    
    def clear_screen(self):
        """Limpiar pantalla"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def print_header(self, title: str):
        """Imprimir encabezado"""
        print("\n" + "="*60)
        print(f"💰 {title}")
        print("="*60 + "\n")
    
    def print_success(self, msg: str):
        """Imprimir mensaje de éxito"""
        print(f"✅ {msg}")
    
    def print_error(self, msg: str):
        """Imprimir mensaje de error"""
        print(f"❌ {msg}")
    
    def print_info(self, msg: str):
        """Imprimir mensaje informativo"""
        print(f"ℹ️  {msg}")
    
    def save_config(self):
        """Guardar configuración (token)"""
        config = {
            "base_url": self.base_url,
            "token": self.token,
            "user": self.user,
            "timestamp": datetime.now().isoformat()
        }
        with open(self.config_file, "w") as f:
            json.dump(config, f, indent=2)
    
    def load_config(self):
        """Cargar configuración guardada"""
        if self.config_file.exists():
            try:
                with open(self.config_file, "r") as f:
                    config = json.load(f)
                    self.token = config.get("token")
                    self.user = config.get("user")
                    self.print_info(f"Sesión cargada para: {self.user.get('email') if self.user else 'N/A'}")
            except Exception as e:
                self.print_error(f"Error cargando config: {str(e)}")
    
    def get_headers(self) -> Dict:
        """Obtener headers con token"""
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers
    
    def make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Optional[Dict]:
        """Hacer solicitud HTTP"""
        url = f"{self.base_url}{endpoint}"
        headers = self.get_headers()
        
        try:
            if method == "GET":
                response = requests.get(url, headers=headers, timeout=10)
            elif method == "POST":
                response = requests.post(url, json=data, headers=headers, timeout=10)
            elif method == "PUT":
                response = requests.put(url, json=data, headers=headers, timeout=10)
            elif method == "DELETE":
                response = requests.delete(url, headers=headers, timeout=10)
            else:
                self.print_error(f"Método HTTP no soportado: {method}")
                return None
            
            if response.status_code in [200, 201]:
                self.print_success(f"Respuesta: {response.status_code}")
                return response.json()
            else:
                self.print_error(f"Error {response.status_code}: {response.text}")
                return None
        
        except requests.exceptions.ConnectionError:
            self.print_error("No se puede conectar al servidor. ¿Está ejecutándose FastAPI?")
            return None
        except Exception as e:
            self.print_error(f"Error en solicitud: {str(e)}")
            return None
    
    def print_json(self, data: Dict):
        """Imprimir JSON formateado"""
        print(json.dumps(data, indent=2, ensure_ascii=False))
    
    # ===== AUTENTICACIÓN =====
    
    def register(self):
        """Registrar nuevo usuario"""
        self.print_header("Registrar Usuario")
        
        email = input("📧 Email: ").strip()
        username = input("👤 Usuario: ").strip()
        password = input("🔐 Contraseña: ").strip()
        
        data = {
            "email": email,
            "username": username,
            "password": password
        }
        
        result = self.make_request("POST", "/auth/register", data)
        if result:
            self.print_json(result)
    
    def login(self):
        """Login de usuario"""
        self.print_header("Login")
        
        email = input("📧 Email: ").strip()
        password = input("🔐 Contraseña: ").strip()
        
        data = {
            "email": email,
            "password": password
        }
        
        result = self.make_request("POST", "/auth/login", data)
        if result:
            self.token = result.get("access_token")
            self.user = result.get("user")
            self.save_config()
            self.print_json(result)
            self.print_success("Sesión iniciada")
    
    def logout(self):
        """Cerrar sesión"""
        self.token = None
        self.user = None
        self.save_config()
        self.print_success("Sesión cerrada")
    
    def get_profile(self):
        """Obtener perfil del usuario"""
        self.print_header("Mi Perfil")
        
        result = self.make_request("GET", "/auth/profile")
        if result:
            self.print_json(result)
    
    # ===== PORTFOLIO =====
    
    def get_portfolio_summary(self):
        """Obtener resumen de portfolio"""
        self.print_header("Resumen de Portfolio")
        
        result = self.make_request("GET", "/portfolio/summary")
        if result:
            self.print_json(result)
    
    def get_portfolio_comprehensive(self):
        """Obtener portfolio comprehensivo"""
        self.print_header("Portfolio Comprehensivo")
        
        network = input("Red (ethereum/arbitrum/polygon): ").strip().lower()
        
        result = self.make_request("GET", f"/portfolio/comprehensive?network={network}")
        if result:
            self.print_json(result)
    
    def get_portfolio_assets(self):
        """Obtener activos del portfolio"""
        self.print_header("Activos del Portfolio")
        
        result = self.make_request("GET", "/portfolio/assets")
        if result:
            self.print_json(result)
    
    # ===== WALLETS =====
    
    def list_wallets(self):
        """Listar wallets"""
        self.print_header("Mis Wallets")
        
        result = self.make_request("GET", "/wallets")
        if result:
            if isinstance(result, list):
                for i, wallet in enumerate(result, 1):
                    print(f"\n{i}. {wallet.get('name', 'N/A')}")
                    print(f"   Dirección: {wallet.get('address', 'N/A')}")
                    print(f"   Red: {wallet.get('network', 'N/A')}")
                    print(f"   Balance: {wallet.get('balance', 'N/A')}")
            else:
                self.print_json(result)
    
    def add_wallet(self):
        """Agregar nueva wallet"""
        self.print_header("Agregar Nueva Wallet")
        
        name = input("📝 Nombre: ").strip()
        address = input("📬 Dirección: ").strip()
        network = input("🌐 Red (ethereum/arbitrum/polygon): ").strip().lower()
        
        data = {
            "name": name,
            "address": address,
            "network": network
        }
        
        result = self.make_request("POST", "/wallets", data)
        if result:
            self.print_json(result)
            self.print_success("Wallet agregada")
    
    def delete_wallet(self):
        """Eliminar wallet"""
        self.print_header("Eliminar Wallet")
        
        wallet_id = input("ID de wallet: ").strip()
        
        result = self.make_request("DELETE", f"/wallets/{wallet_id}")
        if result:
            self.print_success("Wallet eliminada")
    
    # ===== INTERCAMBIOS =====
    
    def list_exchanges(self):
        """Listar intercambios"""
        self.print_header("Mis Intercambios")
        
        result = self.make_request("GET", "/exchanges")
        if result:
            if isinstance(result, list):
                for i, exchange in enumerate(result, 1):
                    print(f"\n{i}. {exchange.get('name', 'N/A')}")
                    print(f"   API Key: {'***' + exchange.get('api_key', 'N/A')[-4:]}")
                    print(f"   Balance: {exchange.get('balance', 'N/A')}")
            else:
                self.print_json(result)
    
    def add_exchange(self):
        """Agregar intercambio"""
        self.print_header("Agregar Intercambio")
        
        name = input("Nombre (binance/kraken/coinbase): ").strip().lower()
        api_key = input("API Key: ").strip()
        api_secret = input("API Secret: ").strip()
        
        data = {
            "name": name,
            "api_key": api_key,
            "api_secret": api_secret
        }
        
        result = self.make_request("POST", "/exchanges", data)
        if result:
            self.print_json(result)
            self.print_success("Intercambio agregado")
    
    # ===== TOKENS =====
    
    def list_tokens(self):
        """Listar tokens monitoreados"""
        self.print_header("Tokens Monitoreados")
        
        result = self.make_request("GET", "/tokens")
        if result:
            if isinstance(result, list):
                for i, token in enumerate(result, 1):
                    print(f"\n{i}. {token.get('symbol', 'N/A').upper()}")
                    print(f"   Precio: ${token.get('price', 'N/A')}")
                    print(f"   24h Change: {token.get('change_24h', 'N/A')}%")
                    print(f"   Market Cap: {token.get('market_cap', 'N/A')}")
            else:
                self.print_json(result)
    
    def add_token(self):
        """Agregar token a monitoreo"""
        self.print_header("Agregar Token")
        
        symbol = input("Símbolo (BTC/ETH/SOL): ").strip().upper()
        coingecko_id = input("CoinGecko ID: ").strip().lower()
        
        data = {
            "symbol": symbol,
            "coingecko_id": coingecko_id
        }
        
        result = self.make_request("POST", "/tokens", data)
        if result:
            self.print_json(result)
            self.print_success("Token agregado")
    
    # ===== DEFI =====
    
    def list_defi_positions(self):
        """Listar posiciones DeFi"""
        self.print_header("Posiciones DeFi")
        
        result = self.make_request("GET", "/defi/positions")
        if result:
            if isinstance(result, list):
                for i, pos in enumerate(result, 1):
                    print(f"\n{i}. {pos.get('protocol', 'N/A')}")
                    print(f"   Tipo: {pos.get('type', 'N/A')}")
                    print(f"   Token: {pos.get('token', 'N/A')}")
                    print(f"   Amount: {pos.get('amount', 'N/A')}")
                    print(f"   APY: {pos.get('apy', 'N/A')}%")
            else:
                self.print_json(result)
    
    def add_defi_position(self):
        """Agregar posición DeFi"""
        self.print_header("Agregar Posición DeFi")
        
        protocol = input("Protocolo (Uniswap/Aave/Curve): ").strip()
        pos_type = input("Tipo (liquidity_pool/lending/staking): ").strip()
        token = input("Token: ").strip().upper()
        amount = float(input("Amount: ").strip())
        
        data = {
            "protocol": protocol,
            "type": pos_type,
            "token": token,
            "amount": amount
        }
        
        result = self.make_request("POST", "/defi/positions", data)
        if result:
            self.print_json(result)
            self.print_success("Posición DeFi agregada")
    
    # ===== REPORTES =====
    
    def get_performance_report(self):
        """Obtener reporte de rendimiento"""
        self.print_header("Reporte de Rendimiento")
        
        period = input("Período (daily/weekly/monthly): ").strip().lower()
        
        result = self.make_request("GET", f"/reports/performance?period={period}")
        if result:
            self.print_json(result)
    
    def get_asset_allocation(self):
        """Obtener asignación de activos"""
        self.print_header("Asignación de Activos")
        
        result = self.make_request("GET", "/reports/asset-allocation")
        if result:
            self.print_json(result)
    
    def get_transactions_history(self):
        """Obtener historial de transacciones"""
        self.print_header("Historial de Transacciones")
        
        limit = input("Número de transacciones (default 20): ").strip()
        limit = int(limit) if limit else 20
        
        result = self.make_request("GET", f"/reports/transactions?limit={limit}")
        if result:
            if isinstance(result, list):
                for i, tx in enumerate(result, 1):
                    print(f"\n{i}. {tx.get('type', 'N/A').upper()}")
                    print(f"   Token: {tx.get('token', 'N/A')}")
                    print(f"   Amount: {tx.get('amount', 'N/A')}")
                    print(f"   Valor: ${tx.get('value', 'N/A')}")
                    print(f"   Fecha: {tx.get('timestamp', 'N/A')}")
            else:
                self.print_json(result)
    
    # ===== MENÚS =====
    
    def menu_auth(self):
        """Menú de autenticación"""
        while True:
            self.print_header("🔐 Autenticación")
            print("1. Registrarse")
            print("2. Login")
            print("3. Ver Perfil")
            print("4. Logout")
            print("0. Volver al menú principal\n")
            
            choice = input("Selecciona opción: ").strip()
            
            if choice == "1":
                self.register()
            elif choice == "2":
                self.login()
            elif choice == "3":
                self.get_profile()
            elif choice == "4":
                self.logout()
            elif choice == "0":
                break
            else:
                self.print_error("Opción inválida")
            
            input("\nPresiona Enter para continuar...")
            self.clear_screen()
    
    def menu_portfolio(self):
        """Menú de portfolio"""
        while True:
            self.print_header("💼 Portfolio")
            print("1. Ver Resumen")
            print("2. Portfolio Comprehensivo")
            print("3. Activos")
            print("0. Volver al menú principal\n")
            
            choice = input("Selecciona opción: ").strip()
            
            if choice == "1":
                self.get_portfolio_summary()
            elif choice == "2":
                self.get_portfolio_comprehensive()
            elif choice == "3":
                self.get_portfolio_assets()
            elif choice == "0":
                break
            else:
                self.print_error("Opción inválida")
            
            input("\nPresiona Enter para continuar...")
            self.clear_screen()
    
    def menu_wallets(self):
        """Menú de wallets"""
        while True:
            self.print_header("🔑 Wallets")
            print("1. Listar Wallets")
            print("2. Agregar Wallet")
            print("3. Eliminar Wallet")
            print("0. Volver al menú principal\n")
            
            choice = input("Selecciona opción: ").strip()
            
            if choice == "1":
                self.list_wallets()
            elif choice == "2":
                self.add_wallet()
            elif choice == "3":
                self.delete_wallet()
            elif choice == "0":
                break
            else:
                self.print_error("Opción inválida")
            
            input("\nPresiona Enter para continuar...")
            self.clear_screen()
    
    def menu_exchanges(self):
        """Menú de intercambios"""
        while True:
            self.print_header("📊 Intercambios")
            print("1. Listar Intercambios")
            print("2. Agregar Intercambio")
            print("0. Volver al menú principal\n")
            
            choice = input("Selecciona opción: ").strip()
            
            if choice == "1":
                self.list_exchanges()
            elif choice == "2":
                self.add_exchange()
            elif choice == "0":
                break
            else:
                self.print_error("Opción inválida")
            
            input("\nPresiona Enter para continuar...")
            self.clear_screen()
    
    def menu_tokens(self):
        """Menú de tokens"""
        while True:
            self.print_header("🪙 Tokens")
            print("1. Listar Tokens")
            print("2. Agregar Token")
            print("0. Volver al menú principal\n")
            
            choice = input("Selecciona opción: ").strip()
            
            if choice == "1":
                self.list_tokens()
            elif choice == "2":
                self.add_token()
            elif choice == "0":
                break
            else:
                self.print_error("Opción inválida")
            
            input("\nPresiona Enter para continuar...")
            self.clear_screen()
    
    def menu_defi(self):
        """Menú de DeFi"""
        while True:
            self.print_header("🔄 DeFi")
            print("1. Listar Posiciones")
            print("2. Agregar Posición")
            print("0. Volver al menú principal\n")
            
            choice = input("Selecciona opción: ").strip()
            
            if choice == "1":
                self.list_defi_positions()
            elif choice == "2":
                self.add_defi_position()
            elif choice == "0":
                break
            else:
                self.print_error("Opción inválida")
            
            input("\nPresiona Enter para continuar...")
            self.clear_screen()
    
    def menu_reports(self):
        """Menú de reportes"""
        while True:
            self.print_header("📈 Reportes")
            print("1. Reporte de Rendimiento")
            print("2. Asignación de Activos")
            print("3. Historial de Transacciones")
            print("0. Volver al menú principal\n")
            
            choice = input("Selecciona opción: ").strip()
            
            if choice == "1":
                self.get_performance_report()
            elif choice == "2":
                self.get_asset_allocation()
            elif choice == "3":
                self.get_transactions_history()
            elif choice == "0":
                break
            else:
                self.print_error("Opción inválida")
            
            input("\nPresiona Enter para continuar...")
            self.clear_screen()
    
    def main_menu(self):
        """Menú principal"""
        while True:
            self.clear_screen()
            
            status = f"✅ Autenticado: {self.user.get('email')}" if self.user else "❌ No autenticado"
            print("\n" + "="*60)
            print("💰 CRYPTO PORTFOLIO DASHBOARD - CLI")
            print("="*60)
            print(f"\n{status}\n")
            
            print("🔐 Autenticación")
            print("1. Menú de Autenticación")
            print("\n💼 Portfolio")
            print("2. Menú de Portfolio")
            print("\n🔑 Wallets")
            print("3. Menú de Wallets")
            print("\n📊 Intercambios")
            print("4. Menú de Intercambios")
            print("\n🪙 Tokens")
            print("5. Menú de Tokens")
            print("\n🔄 DeFi")
            print("6. Menú de DeFi")
            print("\n📈 Reportes")
            print("7. Menú de Reportes")
            print("\n0. Salir\n")
            
            choice = input("Selecciona opción: ").strip()
            
            if choice == "1":
                self.menu_auth()
            elif choice == "2":
                self.menu_portfolio()
            elif choice == "3":
                self.menu_wallets()
            elif choice == "4":
                self.menu_exchanges()
            elif choice == "5":
                self.menu_tokens()
            elif choice == "6":
                self.menu_defi()
            elif choice == "7":
                self.menu_reports()
            elif choice == "0":
                self.print_success("¡Hasta luego!")
                break
            else:
                self.print_error("Opción inválida")
                time.sleep(1)


def main():
    """Punto de entrada"""
    
    # Verificar si FastAPI está corriendo
    cli = CryptoDashboardCLI()
    
    print("\n" + "="*60)
    print("🚀 INICIANDO CLI - Crypto Portfolio Dashboard")
    print("="*60)
    
    print("\n⏳ Verificando conexión al servidor FastAPI...")
    
    try:
        response = requests.get(f"{cli.base_url}/docs", timeout=5)
        print("✅ Servidor FastAPI detectado\n")
    except:
        print("❌ No se puede conectar a FastAPI en http://localhost:8000")
        print("   Asegúrate de ejecutar: python main.py")
        sys.exit(1)
    
    time.sleep(1)
    cli.main_menu()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Programa interrumpido por usuario")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        sys.exit(1)
