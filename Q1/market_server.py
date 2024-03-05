from datetime import datetime
from concurrent import futures
import grpc
import marketplace_pb2
import marketplace_pb2_grpc

class MarketplaceService(marketplace_pb2_grpc.MarketplaceServicer):
    def __init__(self):
        '''
        Defines the functionality of the marketplace service.
        This is the server-side implementation of the gRPC service.
        '''
        self.sellers = {}  # Maps UUID to seller details
        self.items = {}  # Maps item ID to item details
        self.wishlist = {}  # Maps buyer_address to a list of item_ids
        self.item_watchers = {}  # New: Maps item_id to a list of buyer_addresses
        self.notifications = {}  # Maps buyer_address to a list of notification messages
        self.seller_notifications = {}  # Maps seller UUID to a list of notification messages
        self.ratings = {}  # New: Maps item_id to a list of (buyer_address, rating)
        self.next_item_id = 1

    def identify_interested_buyers(self, item_id):
        '''
        Return a list of buyers interested in the given item_id.
        '''
        return self.item_watchers.get(item_id, [])

    def RegisterSeller(self, request, context):
        '''
        Register a new seller with the marketplace.
        '''
        print(f"{datetime.now()} - Seller join request from {request.ip_port}, uuid = {request.uuid}")
        if request.uuid in self.sellers:
            return marketplace_pb2.OperationResponse(success=False, message="UUID already registered")
        self.sellers[request.uuid] = {"ip_port": request.ip_port}
        return marketplace_pb2.OperationResponse(success=True, message="Seller registered successfully")

    def AddItem(self, request, context):
        '''
        Add a new item to the marketplace.
        '''
        print(f"{datetime.now()} - Add Item request from {request.uuid}")
        if request.uuid not in self.sellers:
            return marketplace_pb2.OperationResponse(success=False, message="Seller UUID not recognized")
        item = request.item
        item.id = self.next_item_id
        self.items[self.next_item_id] = item
        self.next_item_id += 1
        return marketplace_pb2.OperationResponse(success=True, message=f"Item added successfully with ID {item.id}")

    def SearchItems(self, request, context):
        '''
        Search for items by name and category.
        '''
        print(f"{datetime.now()} - Search request for Item name: {request.name}, Category: {request.category}")
        result_items = []
        for item in self.items.values():
            if (request.category == marketplace_pb2.Category.ANY or item.category == request.category) and (request.name.lower() in item.name.lower() or not request.name):
                # Check if the item has been rated
                if item.id in self.ratings:
                    total_ratings = sum(rating for _, rating in self.ratings[item.id])
                    average_rating = total_ratings / len(self.ratings[item.id])
                    item.rating = average_rating
                else:
                    item.rating = -1
                result_items.append(item)
        return marketplace_pb2.SearchResponse(items=result_items)

    def DisplaySellerItems(self, request, context):
        '''
        Display items for a specific seller.
        '''
        if request.uuid not in self.sellers:
            return marketplace_pb2.DisplaySellerItemsResponse()  # Seller not found or other error handling

        seller_items = []
        for item in self.items.values():
            if item.seller_address.endswith(request.uuid):
                # Check if the item has been rated
                if item.id in self.ratings:
                    total_ratings = sum(rating for _, rating in self.ratings[item.id])
                    average_rating = total_ratings / len(self.ratings[item.id])
                    item.rating = average_rating
                else:
                    item.rating = -1
                seller_items.append(item)
        return marketplace_pb2.DisplaySellerItemsResponse(items=seller_items)
    
    def DeleteItem(self, request, context):
        '''
        Delete an item from the marketplace.
        '''
        print(f"{datetime.now()} - Delete Item {request.id} request from {request.uuid}")
        if request.uuid not in self.sellers:
            return marketplace_pb2.OperationResponse(success=False, message="Seller UUID not recognized")
        if request.id in self.items:
            del self.items[request.id]
            return marketplace_pb2.OperationResponse(success=True, message="Item deleted successfully")
        else:
            return marketplace_pb2.OperationResponse(success=False, message="Item ID not found")
        
    def UpdateItem(self, request, context):
        '''
        Update an item in the marketplace.
        '''
        print(f"{datetime.now()} - Update Item {request.id} request from {request.uuid}")
        if request.uuid not in self.sellers:
            return marketplace_pb2.OperationResponse(success=False, message="Seller UUID not recognized")
        if request.id not in self.items:
            return marketplace_pb2.OperationResponse(success=False, message="Item ID not found")
        
        item = self.items[request.id]
        item.quantity = request.quantity
        item.price = request.price
        self.notify_buyers(request.id, "updated")
        return marketplace_pb2.OperationResponse(success=True, message="Item updated successfully")
    
    def BuyItem(self, request, context):
        '''
        Buy an item from the marketplace.
        '''
        print(f"{datetime.now()} - Buy request {request.quantity} of item {request.item_id}, from {request.buyer_address}")
        if request.item_id not in self.items:
            return marketplace_pb2.OperationResponse(success=False, message="Item not found")
        item = self.items[request.item_id]
        if item.quantity < request.quantity:
            return marketplace_pb2.OperationResponse(success=False, message="Not enough stock available")
        item.quantity -= request.quantity
        seller_uuid = self.find_seller_uuid_by_item_id(request.item_id)
        if seller_uuid:
            self.notify_seller(seller_uuid, item, request.quantity, request.buyer_address)

        self.notify_buyers(request.item_id, "purchased")
        return marketplace_pb2.OperationResponse(success=True, message="Purchase successful")

    def RateItem(self, request, context):
        '''
        Rate an item in the marketplace.
        '''
        # Existing rate item
        if request.item_id not in self.ratings:
            self.ratings[request.item_id] = []
        elif any(buyer_address == request.buyer_address for buyer_address, _ in self.ratings[request.item_id]):
            return marketplace_pb2.OperationResponse(success=False, message="Buyer has already rated this item")
        # Add the new rating
        self.ratings[request.item_id].append((request.buyer_address, request.rating))
        # Update item's average rating
        total_ratings = sum(rating for _, rating in self.ratings[request.item_id])
        average_rating = total_ratings / len(self.ratings[request.item_id])
        item = self.items[request.item_id]  # Assuming this exists from your item addition logic
        item.rating = average_rating  # Assuming your item proto has a rating field
        return marketplace_pb2.OperationResponse(success=True, message="Rating successful, average rating updated.")

    def find_seller_uuid_by_item_id(self, item_id):
        '''
        Find the seller's UUID given an item ID.
        '''
        item = self.items.get(item_id)
        if item:
            print("find seller by uuid by item id", item.seller_address)
            print(item.seller_address)
            return item.seller_address
        return None

    def notify_seller(self, seller_address, item, quantity_sold, buyer_address):
        '''
        Notify the seller of a purchase.
        '''
        print("seller address: ", seller_address)
        # Extract UUID from seller_address
        seller_uuid = seller_address.split(':')[1]  # Adjust based on your actual format
        print("Server UUID:", seller_uuid)

        print("Important, UUID:", seller_uuid)
        
        message = f"Item Sold: {item.name}, Quantity: {quantity_sold}, Buyer: {buyer_address}"
        if seller_uuid not in self.seller_notifications:
            print("This is something I don't understand")
            self.seller_notifications[seller_uuid] = []
        print("Seller UUID in storage")
        self.seller_notifications[seller_uuid].append(message)
        print(f"Notification stored for seller {seller_uuid}: {message}")

    def FetchSellerNotifications(self, request, context):
        '''
        Fetch notifications for a seller.
        '''
        seller_uuid = request.uuid
        notifications = self.seller_notifications.get(seller_uuid, [])
        self.seller_notifications[seller_uuid] = []  
        return marketplace_pb2.NotificationResponse(messages=notifications)
    
    def FetchNotifications(self, request, context):
        '''
        Fetch notifications for a buyer.
        '''
        messages = self.notifications.get(request.buyer_address, [])
        if messages:
            print(f"{datetime.now()} - Sending notifications to {request.buyer_address}: {messages}")
        # Clear notifications after fetching
        self.notifications[request.buyer_address] = []
        return marketplace_pb2.NotificationResponse(messages=messages)
    
    def notify_buyers(self, item_id, action):
        '''
        Notify buyers interested in an item about updates or purchases.
        '''
        interested_buyers = self.item_watchers.get(item_id, [])
        if item_id in self.items:
            item = self.items[item_id]
            # Format the item details into a notification message
            notification_message = f"\n#######\n\nThe Following Item has been {action}:\n\n" \
                                f"Item ID: {item.id}, Price: ${item.price}, Name: {item.name}, " \
                                f"Category: {self.get_category_name(item.category)},\n" \
                                f"Description: {item.description}.\n" \
                                f"Quantity Remaining: {item.quantity}\n" \
                                f"Rating: {item.rating} / 5  |  Seller: {item.seller_address}\n\n#######"
            for buyer in interested_buyers:
                if buyer not in self.notifications:
                    self.notifications[buyer] = []
                self.notifications[buyer].append(notification_message)
                print(f"{datetime.now()} - Notification stored for {buyer}: Item {item_id} has been {action}.")
        else:
            print(f"{datetime.now()} - Attempted to notify buyers for a non-existent item: {item_id}.")

    def get_category_name(self, category):
        '''
        Convert category enum to a readable string.
        '''
        category_names = {marketplace_pb2.Category.ELECTRONICS: "Electronics",
                        marketplace_pb2.Category.FASHION: "Fashion",
                        marketplace_pb2.Category.OTHERS: "Others"}
        return category_names.get(category, "Unknown")
    
    def AddToWishList(self, request, context):
        '''
        Add an item to a buyer's wishlist.
        '''
        if request.item_id not in self.items:
            print(f"{datetime.now()} - Wishlist addition failed: Item {request.item_id} not found for {request.buyer_address}.")
            return marketplace_pb2.OperationResponse(success=False, message="Item not found")

        if request.buyer_address not in self.wishlist:
            self.wishlist[request.buyer_address] = []
        
        if request.item_id not in self.wishlist[request.buyer_address]:
            self.wishlist[request.buyer_address].append(request.item_id)
            # Update 'item_watchers' for notification purposes
            if request.item_id not in self.item_watchers:
                self.item_watchers[request.item_id] = []
            self.item_watchers[request.item_id].append(request.buyer_address)
            
            print(f"{datetime.now()} - Item {request.item_id} added to wishlist for {request.buyer_address}.")
            return marketplace_pb2.OperationResponse(success=True, message="Item added to wishlist")
        else:
            print(f"{datetime.now()} - Item {request.item_id} already in wishlist for {request.buyer_address}.")
            return marketplace_pb2.OperationResponse(success=False, message="Item already in wishlist")

def serve():
    '''
    Start the server.
    '''
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    marketplace_pb2_grpc.add_MarketplaceServicer_to_server(MarketplaceService(), server)
    server.add_insecure_port('[::]:50051')
    print("Market Server started. Listening on port 50051.")
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    serve()