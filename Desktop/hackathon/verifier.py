 from web3 import Web3
import os

class CredentialVerifier:
    def __init__(self, provider_url, contract_address, abi):
        self.w3 = Web3(Web3.HTTPProvider(provider_url))
        self.contract = self.w3.eth.contract(address=contract_address, abi=abi)

    def check_degree(self, student_wallet):
        """Checks if a degree exists on the blockchain."""
        try:
            is_valid = self.contract.functions.verify(student_wallet).call()
            return is_valid
        except Exception as e:
            return False
            