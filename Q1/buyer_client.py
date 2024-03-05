import threading
import time
import grpc
import uuid
import marketplace_pb2
import marketplace_pb2_grpc

SERVER_ADDRESS = "10.190.0.2:50051"
SELLER_ADDRESS = "10.190.0.4" 

class BuyerClient:
    def __init__(self, address):
        '''
        Client for the buyer to interact with the marketplace.
        '''
        self.channel = grpc.insecure_channel(address)
        self.stub = marketplace_pb2_grpc.MarketplaceStub(self.channel)
        self.uuid = str(uuid.uuid4())
        self.buyer_address = f"{SELLER_ADDRESS}:{self.uuid[:8]}"  # Mock IP:Port with UUID

    def search_items(self, name="", category=marketplace_pb2.ANY):
        """Search for items by name and category."""
        try:
            response = self.stub.SearchItems(marketplace_pb2.SearchRequest(name=name, category=category))
            print("Search Results:")
            for item in response.items:
                rating = item.rating if item.rating != -1 else "UNRATED"
                print(f"Item ID: {item.id}, Name: {item.name}, Price: ${item.price}, Quantity: {item.quantity}, Rating: {rating}")
            return response.items
        except grpc.RpcError as e:
            print(f"SearchItems failed with {e.code()}: {e.details()}")

    def buy_item(self, item_id, quantity):
        """Buy an item specifying its ID and the desired quantity."""
        try:
            response = self.stub.BuyItem(marketplace_pb2.BuyItemRequest(
                item_id=item_id, quantity=quantity, buyer_address=self.buyer_address))
            print(f"BuyItem response: {response.message}")
        except grpc.RpcError as e:
            print(f"BuyItem failed with {e.code()}: {e.details()}")

    def add_to_wishlist(self, item_id):
        """Add an item to the wishlist."""
        try:
            response = self.stub.AddToWishList(marketplace_pb2.WishlistRequest(
                item_id=item_id, buyer_address=self.buyer_address))
            print(f"AddToWishList response: {response.message}")
        except grpc.RpcError as e:
            print(f"AddToWishList failed with {e.code()}: {e.details()}")

    def rate_item(self, item_id, rating):
        """Rate an item."""
        try:
            response = self.stub.RateItem(marketplace_pb2.RateItemRequest(
                item_id=item_id, rating=rating, buyer_address=self.buyer_address))
            print(f"RateItem response: {response.message}")
        except grpc.RpcError as e:
            print(f"RateItem failed with {e.code()}: {e.details()}")

    def fetch_notifications(self):
        """Fetch and display notifications."""
        response = self.stub.FetchNotifications(
            marketplace_pb2.NotificationRequest(buyer_address=self.buyer_address))
        # print("there hsoudl be printintg")
        for message in response.messages:
            print(f"Notification: {message}")

    def start_notification_listener(self):
        """Periodically fetch notifications in the background."""
        def listener():
            while True:
                self.fetch_notifications()
                time.sleep(5)  # Adjust the frequency as needed

        thread = threading.Thread(target=listener)
        thread.daemon = True
        thread.start()
    

def buyer_menu(client):
    '''
    Buyer menu for interacting with the marketplace.
    '''
    while True:
        print("\n===== Buyer Menu =====")
        print("1. Search Items")
        print("2. Buy Item")
        print("3. Add Item to Wishlist")
        print("4. Rate Item")
        print("5. Exit")
        choice = input("Enter your choice: ")

        if choice == "1":
            name = input("Enter item name (leave blank to list all): ")
            category = input("Enter item category (ELECTRONICS, FASHION, OTHERS, ANY): ")
            if category == "":
                category = "ANY"
            client.search_items(name, marketplace_pb2.Category.Value(category))
        elif choice == "2":
            item_id = int(input("Enter item ID to buy: "))
            quantity = int(input("Enter quantity: "))
            client.buy_item(item_id, quantity)
        elif choice == "3":
            item_id = int(input("Enter item ID to add to wishlist: "))
            client.add_to_wishlist(item_id)
        elif choice == "4":
            item_id = int(input("Enter item ID to rate: "))
            rating = int(input("Enter rating (1-5): "))
            if (rating > 5):
                rating = 5
            if (rating < 1):
                rating = 1
            client.rate_item(item_id, rating)
        elif choice == "5":
            print("Exiting...")
            break
        else:
            print("Invalid choice. Please try again.")


def main():
    '''
    Start the buyer client.
    '''
    client = BuyerClient(SERVER_ADDRESS)
    client.start_notification_listener()
    threading.Thread(target=client.fetch_notifications, daemon=True).start()
    buyer_menu(client)

if __name__ == "__main__":
    main()