from __future__ import print_function
import datetime
from stellar_sdk import Network, Keypair, Server, TransactionBuilder, Asset, Claimant, ClaimPredicate


class Stellar:
    def __init__(self):
        self.startBalance = "5"
        self.startBonusAmount = "1000"
        self.network_passphrase = Network.TESTNET_NETWORK_PASSPHRASE
        self.horizon = "https://horizon-testnet.stellar.org"
        self.bet_token = "SIA"
        self.bet_token_issuer = "GAMZPLI7CBKROXUN7EJSB3AULOTDL4THCOILARH37F7S3CELQPJ74V6A"
        self.airdrop_account = "SAUH24ZZEQR3L6IM55M7SZGSQSV4Q3SADBLGETU7DQ7L6NKJUK2EHGKH"
        self.escrowAccount = "GARGKKUCSMXEF5YCWTJ5NX375ZJSPLKOZUK3J3KJE4H2GD4VATZJ6VEN"
        self.escrowAccountPvKey = "SDYOLSYNOZ3Q3VLCMLFVZORTMC67VMEOZAK23C47AXJOSM3TUP4TXMFU"

        # SC2L6VIBFGBA2MTVLF4CLFGJLFKKPQHTHUNKDZJWJXPWG4XR6QZ4ZYVQ-ISSuer
        # SDYOLSYNOZ3Q3VLCMLFVZORTMC67VMEOZAK23C47AXJOSM3TUP4TXMFU-escrowAccount
        # SAUH24ZZEQR3L6IM55M7SZGSQSV4Q3SADBLGETU7DQ7L6NKJUK2EHGKH-DIS-GB4LHBRH53LPXIVUEEBA2DA3S36HWU4VJGZ4CVYERFVA4ZAG47IX4SGW

    def claim_claimable_balance(self, claimant_secret, sponser_id):
        claimant_secret = Keypair.from_secret(claimant_secret)
        server = Server(self.horizon)
        sender_account = server.load_account(claimant_secret.public_key)
        base_fee = server.fetch_base_fee()
        bet_asset = Asset(self.bet_token, self.bet_token_issuer)
        balance = server.claimable_balances().for_claimant(claimant_secret.public_key).call()
        for x in balance:
            print(x)

        print(balance)
        return balance

    def create_claimable_balance(self, sender_secret, recipient_public_key, amount, memo):
        sender_keypair = Keypair.from_secret(sender_secret)
        server = Server(self.horizon)
        sender_account = server.load_account(sender_keypair.public_key)
        base_fee = server.fetch_base_fee()
        bet_asset = Asset(self.bet_token, self.bet_token_issuer)

        x = datetime.datetime.now()
        y = x + datetime.timedelta(0, 60)
        soon = int(y.timestamp())

        bCanClaim = ClaimPredicate.predicate_before_relative_time(60)
        aCanReclaim = ClaimPredicate.predicate_not(ClaimPredicate.predicate_before_absolute_time(soon))

        claimants_list = [
            Claimant(recipient_public_key, bCanClaim),
            Claimant(sender_keypair.public_key, aCanReclaim)
        ]

        transaction = (
            TransactionBuilder(
                source_account=sender_account,
                network_passphrase=self.network_passphrase,
                base_fee=base_fee,
            )
                .add_text_memo(memo)
                .append_create_claimable_balance_op(asset=bet_asset, amount=amount, claimants=claimants_list)
                .build()
        )
        transaction.sign(sender_keypair)
        response = server.submit_transaction(transaction)
        return response['hash']

    def bet_match_claimable_balance(self, sender_keypair, opponent_keypair, amount, memo):
        server = Server(self.horizon)

        sender_public_key = sender_keypair.public_key
        opponent_public_key = opponent_keypair.public_key

        sender_account = server.load_account(sender_public_key)
        base_fee = server.fetch_base_fee()
        bet_asset = Asset(self.bet_token, self.bet_token_issuer)

        x = datetime.datetime.now()
        y = x + datetime.timedelta(0, 60)
        soon = int(y.timestamp())

        opponent_can_claim = ClaimPredicate.predicate_before_relative_time(60)
        sender_can_reclaim = ClaimPredicate.predicate_not(ClaimPredicate.predicate_before_absolute_time(soon))

        sender_claimants_list = [
            Claimant(opponent_public_key, opponent_can_claim),
            Claimant(sender_public_key, sender_can_reclaim)
        ]

        sender_can_claim = ClaimPredicate.predicate_before_relative_time(60)
        opponent_can_reclaim = ClaimPredicate.predicate_not(ClaimPredicate.predicate_before_absolute_time(soon))

        opponent_claimants_list = [
            Claimant(sender_public_key, sender_can_claim),
            Claimant(opponent_public_key, opponent_can_reclaim)
        ]

        transaction = (
            TransactionBuilder(
                source_account=sender_account,
                network_passphrase=self.network_passphrase,
                base_fee=base_fee,
            )
                .add_text_memo(memo)
                .append_create_claimable_balance_op(asset=bet_asset, amount=amount, claimants=sender_claimants_list)
                .append_create_claimable_balance_op(asset=bet_asset, amount=amount, claimants=opponent_claimants_list,
                                                    source=opponent_public_key)
                .build()
        )
        transaction.sign(sender_keypair)
        transaction.sign(opponent_keypair)
        response = server.submit_transaction(transaction)
        return response['hash']

    def sponsor_account(self, public_key, receiver_keypair):
        sender_keypair = Keypair.from_secret(self.airdrop_account)

        server = Server(self.horizon)
        sender_account = server.load_account(sender_keypair.public_key)
        base_fee = server.fetch_base_fee()
        transaction = (
            TransactionBuilder(
                source_account=sender_account,
                network_passphrase=self.network_passphrase,
                base_fee=base_fee,
            ).add_text_memo("sponsered_account")
                .append_begin_sponsoring_future_reserves_op(public_key)
                .append_create_account_op(public_key, self.startBalance)
                .append_change_trust_op(self.bet_token, self.bet_token_issuer, source=public_key)
                .append_payment_op(receiver_keypair.public_key, self.startBonusAmount, asset_code=self.bet_token,
                                   asset_issuer=self.bet_token_issuer)
                .append_end_sponsoring_future_reserves_op(public_key)

                .build()
        )
        transaction.sign(sender_keypair)
        transaction.sign(receiver_keypair)
        response = server.submit_transaction(transaction)
        return response

    def make_payment(self, sender_keypair, recipient_public_key, asset_code, asset_issuer, amount, memo):
        server = Server(self.horizon)
        print(sender_keypair.public_key)
        sender_account = server.load_account(sender_keypair.public_key)
        base_fee = server.fetch_base_fee()
        transaction = (
            TransactionBuilder(
                source_account=sender_account,
                network_passphrase=self.network_passphrase,
                base_fee=base_fee,
            )
                .add_text_memo(memo)
                .append_payment_op(recipient_public_key, amount, asset_code,
                                   asset_issuer).build()
        )
        transaction.sign(sender_keypair)
        response = server.submit_transaction(transaction)
        return response['hash']


def generate_keys():
    return Keypair.random()


stellar = Stellar()
if __name__ == '__main__':
    stellar().Init()
