"""
Seed script to populate the database with sample dress products
Run this after starting the backend server
"""

import requests
import json

BASE_URL = "http://localhost:8000"

# Sample dress products with real Unsplash images
SAMPLE_PRODUCTS = [
    {
        "name": "Elegant Evening Gown",
        "description": "Stunning floor-length evening gown perfect for galas and formal events. Features a fitted bodice and flowing skirt with subtle shimmer.",
        "price": 189.99,
        "stock": 12,
        "image_url": "https://images.unsplash.com/photo-1595777457583-95e059d581b8?w=800",
        "is_listed": True
    },
    {
        "name": "Summer Floral Maxi Dress",
        "description": "Light and breezy maxi dress with beautiful floral print. Perfect for beach weddings or summer garden parties.",
        "price": 79.99,
        "stock": 25,
        "image_url": "https://images.unsplash.com/photo-1566174053879-31528523f8ae?w=800",
        "is_listed": True
    },
    {
        "name": "Classic Little Black Dress",
        "description": "Timeless LBD that works for any occasion. Knee-length with a flattering A-line silhouette and elegant neckline.",
        "price": 129.99,
        "stock": 18,
        "image_url": "https://images.unsplash.com/photo-1572804013309-59a88b7e92f1?w=800",
        "is_listed": True
    },
    {
        "name": "Cocktail Party Dress",
        "description": "Chic cocktail dress with sequin details and fitted silhouette. Stand out at your next cocktail party or night out.",
        "price": 149.99,
        "stock": 15,
        "image_url": "https://images.unsplash.com/photo-1515372039744-b8f02a3ae446?w=800",
        "is_listed": True
    },
    {
        "name": "Bohemian Wrap Dress",
        "description": "Flowing wrap dress with bohemian print. Adjustable tie waist and flutter sleeves for a comfortable, flattering fit.",
        "price": 89.99,
        "stock": 30,
        "image_url": "https://images.unsplash.com/photo-1496747611176-843222e1e57c?w=800",
        "is_listed": True
    },
    {
        "name": "Professional Sheath Dress",
        "description": "Sophisticated sheath dress perfect for the office or business meetings. Clean lines and professional appearance.",
        "price": 119.99,
        "stock": 20,
        "image_url": "https://images.unsplash.com/photo-1490481651871-ab68de25d43d?w=800",
        "is_listed": True
    },
    {
        "name": "Vintage Lace Dress",
        "description": "Romantic vintage-inspired dress with delicate lace overlay. Perfect for brunches, tea parties, or romantic dates.",
        "price": 139.99,
        "stock": 10,
        "image_url": "https://images.unsplash.com/photo-1585487000143-5b9473ecb77f?w=800",
        "is_listed": True
    },
    {
        "name": "Casual Denim Dress",
        "description": "Versatile denim shirt dress with button-front closure. Dress it up or down for any casual occasion.",
        "price": 69.99,
        "stock": 35,
        "image_url": "https://images.unsplash.com/photo-1551488831-00ddcb6c6bd3?w=800",
        "is_listed": True
    },
    {
        "name": "Red Carpet Gown",
        "description": "Show-stopping red carpet gown with dramatic train and figure-hugging silhouette. Make an unforgettable entrance.",
        "price": 299.99,
        "stock": 5,
        "image_url": "https://images.unsplash.com/photo-1566174053879-31528523f8ae?w=800",
        "is_listed": True
    },
    {
        "name": "Beach Cover-Up Dress",
        "description": "Lightweight, breezy dress perfect as a beach cover-up or for casual summer outings. Quick-dry fabric.",
        "price": 49.99,
        "stock": 40,
        "image_url": "https://images.unsplash.com/photo-1529139574466-a303027c1d8b?w=800",
        "is_listed": True
    },
    {
        "name": "Winter Sweater Dress",
        "description": "Cozy knit sweater dress with turtleneck. Perfect for staying stylish and warm during colder months.",
        "price": 99.99,
        "stock": 22,
        "image_url": "https://images.unsplash.com/photo-1539008835657-9e8e9680c956?w=800",
        "is_listed": True
    },
    {
        "name": "Sundress with Pockets",
        "description": "Fun and functional sundress with hidden pockets. Bright colors and comfortable fit for all-day wear.",
        "price": 59.99,
        "stock": 45,
        "image_url": "https://images.unsplash.com/photo-1595777457583-95e059d581b8?w=800",
        "is_listed": True
    },
    {
        "name": "Midi Wrap Dress",
        "description": "Elegant midi-length wrap dress with tie waist. Flattering on all body types and perfect for semi-formal events.",
        "price": 94.99,
        "stock": 28,
        "image_url": "https://images.unsplash.com/photo-1572804013309-59a88b7e92f1?w=800",
        "is_listed": True
    },
    {
        "name": "Off-Shoulder Party Dress",
        "description": "Trendy off-shoulder dress with ruffled neckline. Perfect for parties, dates, or girls' night out.",
        "price": 84.99,
        "stock": 16,
        "image_url": "https://images.unsplash.com/photo-1515372039744-b8f02a3ae446?w=800",
        "is_listed": True
    },
    {
        "name": "Pleated Midi Dress",
        "description": "Sophisticated pleated dress with elegant draping. Versatile enough for work or weekend events.",
        "price": 109.99,
        "stock": 14,
        "image_url": "https://images.unsplash.com/photo-1490481651871-ab68de25d43d?w=800",
        "is_listed": True
    },
    {
        "name": "Silk Slip Dress",
        "description": "Luxurious silk slip dress with adjustable straps. Ideal for layering or wearing alone on warm evenings.",
        "price": 159.99,
        "stock": 8,
        "image_url": "https://images.unsplash.com/photo-1581565493708-9c78f6c56363?w=800",
        "is_listed": True
    },
    {
        "name": "Embroidered Maxi Dress",
        "description": "Hand-embroidered maxi with intricate floral patterns along the hem. Bohemian elegance for festivals.",
        "price": 179.99,
        "stock": 11,
        "image_url": "https://images.unsplash.com/photo-1607345266089-c96377f9aabc?w=800",
        "is_listed": True
    },
    {
        "name": "Satin Wrap Midi",
        "description": "Smooth satin wrap midi dress with deep V-neckline. Perfect for date nights or dinners.",
        "price": 134.99,
        "stock": 17,
        "image_url": "https://images.unsplash.com/photo-1576638144025-9b3d03b14b1f?w=800",
        "is_listed": True
    },
    {
        "name": "Chiffon Tea Dress",
        "description": "Light chiffon tea dress with puffed sleeves and lace trim. Vintage charm for afternoon teas.",
        "price": 89.99,
        "stock": 24,
        "image_url": "https://images.unsplash.com/photo-1592361103949-60df4d8b4726?w=800",
        "is_listed": True
    },
    {
        "name": "Velvet Evening Dress",
        "description": "Rich velvet evening dress with off-the-shoulder design. Luxe fabric for holiday parties.",
        "price": 219.99,
        "stock": 6,
        "image_url": "https://images.unsplash.com/photo-1608250471251-8d2ef1a7bb72?w=800",
        "is_listed": True
    },
    {
        "name": "Cotton Shirt Dress",
        "description": "Crisp cotton shirt dress with belt and roll-up sleeves. Effortless casual style.",
        "price": 74.99,
        "stock": 32,
        "image_url": "https://images.unsplash.com/photo-1551028719-00167b16eac5?w=800",
        "is_listed": True
    },
    {
        "name": "Lace Mermaid Gown",
        "description": "Fitted lace mermaid gown with dramatic fishtail skirt. Show-stopping for weddings.",
        "price": 249.99,
        "stock": 4,
        "image_url": "https://images.unsplash.com/photo-1519741497674-611481863552?w=800",
        "is_listed": True
    },
    {
        "name": "Jersey Knit Dress",
        "description": "Soft jersey knit bodycon dress. Comfortable stretch fit for everyday wear.",
        "price": 64.99,
        "stock": 38,
        "image_url": "https://images.unsplash.com/photo-1542272604-787c3835535d?w=800",
        "is_listed": True
    },
    {
        "name": "Floral Print Sundress",
        "description": "Playful floral print sundress with spaghetti straps. Breezy for summer outings.",
        "price": 54.99,
        "stock": 41,
        "image_url": "https://images.unsplash.com/photo-1416879595882-3373a0480b5b?w=800",
        "is_listed": True
    },
    {
        "name": "Taffeta Ball Gown",
        "description": "Structured taffeta ball gown with full skirt. Cinderella-worthy for proms or balls.",
        "price": 289.99,
        "stock": 3,
        "image_url": "https://images.unsplash.com/photo-1529139574466-a303027c1d8b?w=800",
        "is_listed": True
    },
    {"name": "Strapless Corset Dress", "description": "Bonéd corset-style strapless dress with sweetheart neckline. Dramatic hourglass figure.", "price": 199.99, "stock": 9, "image_url": "https://images.unsplash.com/photo-1592815522336-7de346215498?w=800", "is_listed": True},
    {"name": "High-Low Hem Dress", "description": "Asymmetric high-low hem dress with ruffle details. Fun and flirty movement.", "price": 99.99, "stock": 26, "image_url": "https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=800", "is_listed": True},
    {"name": "Sequined Shift Dress", "description": "All-over sequin shift dress for nightlife. Straight silhouette, easy slip-on.", "price": 169.99, "stock": 13, "image_url": "https://images.unsplash.com/photo-1600905688600-7e192225d0be?w=800", "is_listed": True},
    {"name": "Peasant Blouse Dress", "description": "Flowy peasant-style dress with elastic cuffs and neckline. Effortless cottagecore.", "price": 79.99, "stock": 31, "image_url": "https://images.unsplash.com/photo-1593786403235-4f90a192e890?w=800", "is_listed": True},
    {"name": "One-Shoulder Gown", "description": "Elegant one-shoulder satin gown with thigh slit. Red carpet glamour.", "price": 259.99, "stock": 7, "image_url": "https://images.unsplash.com/photo-1571883988457-6d9f5a8d1a4a?w=800", "is_listed": True},
    {"name": "Polo Shirt Dress", "description": "Preppy polo collar shirt dress with skort hem. Sporty casual vibe.", "price": 69.99, "stock": 37, "image_url": "https://images.unsplash.com/photo-1620270112612-19ded288e0bd?w=800", "is_listed": True},
    {"name": "Tulle Skirt Dress", "description": "Fitted bodice with layered tulle skirt. Ballerina-inspired romance.", "price": 189.99, "stock": 12, "image_url": "https://images.unsplash.com/photo-1558618047-3c8c76ca7e86?w=800", "is_listed": True},
    {"name": "Modal Slip Maxi", "description": "Ultra-soft modal slip maxi with side slits. Lounge-to-street versatile.", "price": 84.99, "stock": 29, "image_url": "https://images.unsplash.com/photo-1602293589931-0d2a2a8690bf?w=800", "is_listed": True},
    {"name": "Button-Front Sundress", "description": "Lightweight button-front sundress with tiered skirt. Picnic-ready charm.", "price": 59.99, "stock": 44, "image_url": "https://images.unsplash.com/photo-1574250329546-1b5ea6e0e0ee?w=800", "is_listed": True},
    {"name": "Metallic Lamé Dress", "description": "Shiny metallic lamé mini dress with halter neck. Party-ready shine.", "price": 129.99, "stock": 19, "image_url": "https://images.unsplash.com/photo-1577968897966-f27d5cf3c3eb?w=800", "is_listed": True}
]

# Sample reviews with varying ratings
SAMPLE_REVIEWS = [
    {
        "product_index": 0,  # Elegant Evening Gown
        "reviews": [
            {"rating": 5, "comment": "Absolutely stunning! I wore this to a gala and received so many compliments. The fit is perfect and the quality is exceptional.", "session": "user_sarah"},
            {"rating": 5, "comment": "This dress made me feel like a princess. Worth every penny!", "session": "user_emily"},
            {"rating": 4, "comment": "Beautiful dress, runs slightly small. Order one size up.", "session": "user_jessica"}
        ]
    },
    {
        "product_index": 1,  # Summer Floral Maxi
        "reviews": [
            {"rating": 5, "comment": "Perfect for my beach wedding! Light, comfortable, and the floral print is gorgeous.", "session": "user_megan"},
            {"rating": 4, "comment": "Love the style and colors. Fabric is a bit thin but great for hot weather.", "session": "user_amanda"},
            {"rating": 5, "comment": "Best summer dress I've ever owned. Bought two more in different prints!", "session": "user_lisa"}
        ]
    },
    {
        "product_index": 2,  # Classic LBD
        "reviews": [
            {"rating": 5, "comment": "Every woman needs this dress in her wardrobe. Classic, elegant, and versatile.", "session": "user_rachel"},
            {"rating": 5, "comment": "Perfect little black dress. Fits like a dream!", "session": "user_olivia"},
            {"rating": 4, "comment": "Great quality and style. Zipper could be a bit smoother.", "session": "user_sophia"}
        ]
    },
    {
        "product_index": 3,  # Cocktail Party Dress
        "reviews": [
            {"rating": 5, "comment": "The sequins catch the light beautifully! Got so many compliments at the party.", "session": "user_natalie"},
            {"rating": 4, "comment": "Love it! Sequins stay in place and don't scratch. Runs true to size.", "session": "user_grace"}
        ]
    },
    {
        "product_index": 4,  # Bohemian Wrap Dress
        "reviews": [
            {"rating": 5, "comment": "So comfortable and flattering! The wrap style is very forgiving.", "session": "user_hannah"},
            {"rating": 5, "comment": "Perfect for a casual day out or dressed up for dinner. Very versatile!", "session": "user_chloe"},
            {"rating": 5, "comment": "The print is even more beautiful in person. Fabric is soft and breathable.", "session": "user_ava"}
        ]
    },
    {
        "product_index": 5,  # Professional Sheath
        "reviews": [
            {"rating": 5, "comment": "Perfect for the office. Professional yet stylish. I have it in three colors now!", "session": "user_emma"},
            {"rating": 4, "comment": "Great work dress. Comfortable to wear all day. Would recommend!", "session": "user_isabella"}
        ]
    },
    {
        "product_index": 6,  # Vintage Lace
        "reviews": [
            {"rating": 5, "comment": "This dress is absolutely romantic and beautiful. The lace detail is exquisite.", "session": "user_lily"},
            {"rating": 4, "comment": "Lovely vintage style. Lining could be a bit softer but overall very pretty.", "session": "user_maya"}
        ]
    },
    {
        "product_index": 7,  # Casual Denim
        "reviews": [
            {"rating": 5, "comment": "My go-to dress for weekends! Comfortable and easy to style.", "session": "user_zoe"},
            {"rating": 5, "comment": "Love how versatile this is. Can dress it up with heels or keep it casual with sneakers.", "session": "user_aria"},
            {"rating": 4, "comment": "Great casual dress. Pockets are a nice touch!", "session": "user_luna"}
        ]
    },
    {
        "product_index": 8,  # Red Carpet Gown
        "reviews": [
            {"rating": 5, "comment": "I felt like a movie star! This dress is absolutely breathtaking.", "session": "user_stella"},
            {"rating": 5, "comment": "Worth the investment. Wore it to a charity gala and felt amazing all night.", "session": "user_ruby"}
        ]
    },
    {
        "product_index": 11,  # Sundress with Pockets
        "reviews": [
            {"rating": 5, "comment": "Pockets! Love this dress. Bright, fun, and so practical.", "session": "user_violet"},
            {"rating": 5, "comment": "Perfect summer dress. The pockets are deep enough for my phone!", "session": "user_hazel"},
            {"rating": 4, "comment": "Cute dress, great colors. Would love to see more patterns.", "session": "user_ivy"}
        ]
    },
    {"product_index": 15, "reviews": [
        {"rating": 5, "comment": "Silk feels amazing on skin. Perfect fit!", "session": "userkatie"},
        {"rating": 4, "comment": "Gorgeous but delicate—handle with care.", "session": "userbella"}
    ]},
    {"product_index": 16, "reviews": [
        {"rating": 5, "comment": "Embroidery is stunning. Got compliments all night.", "session": "usermia"},
        {"rating": 5, "comment": "True boho vibe, flows beautifully.", "session": "usernova"},
        {"rating": 3, "comment": "Pretty but hem frayed after one wash.", "session": "userjade"}
    ]},
    {"product_index": 17, "reviews": [
        {"rating": 5, "comment": "Flattering wrap style hides my flaws perfectly.", "session": "userleah"},
        {"rating": 4, "comment": "Satin shines nicely, size up for curves.", "session": "userpaige"}
    ]},
    {"product_index": 18, "reviews": [
        {"rating": 5, "comment": "Adorable and comfy for tea parties.", "session": "userella"},
        {"rating": 5, "comment": "Lace details are exquisite!", "session": "userrose"}
    ]},
    {"product_index": 19, "reviews": [
        {"rating": 5, "comment": "Velvet is so luxurious—felt like royalty.", "session": "userlara"},
        {"rating": 4, "comment": "Stunning but dry clean only.", "session": "usergemma"}
    ]},
    {"product_index": 20, "reviews": [
        {"rating": 5, "comment": "Versatile and comfy all day.", "session": "userfiona"},
        {"rating": 5, "comment": "Belt cinches perfectly.", "session": "useriris"}
    ]},
    {"product_index": 21, "reviews": [
        {"rating": 5, "comment": "Mermaid shape is figure-flattering!", "session": "userlola"},
        {"rating": 4, "comment": "Beautiful but restrictive for dancing.", "session": "usermira"}
    ]},
    {"product_index": 22, "reviews": [
        {"rating": 5, "comment": "Stretchy and soft—my new favorite.", "session": "usernora"},
        {"rating": 5, "comment": "Hugs curves just right.", "session": "userophelia"}
    ]},
    {"product_index": 23, "reviews": [
        {"rating": 5, "comment": "Perfect summer dress, super cute print.", "session": "userpipa"},
        {"rating": 4, "comment": "Lightweight, but straps slip a bit.", "session": "userquinn"},
        {"rating": 5, "comment": "Bought in every color!", "session": "usrria"}
    ]},
    {"product_index": 24, "reviews": [
        {"rating": 5, "comment": "Ball gown dreams come true!", "session": "usersteph"},
        {"rating": 5, "comment": "Full skirt twirls amazingly.", "session": "usertessa"}
    ]},
    {"product_index": 25, "reviews": [{"rating": 5, "comment": "Corset cinches perfectly!", "session": "useruna"}, {"rating": 4, "comment": "Stunning but needs support.", "session": "uservera"}]},
    {"product_index": 26, "reviews": [{"rating": 5, "comment": "Love the playful hemline!", "session": "userwilla"}, {"rating": 5, "comment": "Twirls beautifully.", "session": "userxena"}]},
    {"product_index": 27, "reviews": [{"rating": 5, "comment": "Sequins sparkle all night.", "session": "useryara"}, {"rating": 4, "comment": "Sheds a little glitter.", "session": "userzara"}, {"rating": 5, "comment": "Club favorite!", "session": "userabba"}]},
    {"product_index": 28, "reviews": [{"rating": 5, "comment": "Cozy cottagecore perfection.", "session": "userbbba"}, {"rating": 5, "comment": "Elastic is comfy.", "session": "userccca"}]},
    {"product_index": 29, "reviews": [{"rating": 5, "comment": "Slit is sexy and elegant.", "session": "userddda"}, {"rating": 4, "comment": "Fabric wrinkles easily.", "session": "usereeea"}]},
    {"product_index": 30, "reviews": [{"rating": 5, "comment": "Sporty yet cute.", "session": "userfffa"}, {"rating": 5, "comment": "Pockets included!", "session": "userggga"}]},
    {"product_index": 31, "reviews": [{"rating": 5, "comment": "Tulle layers are dreamy.", "session": "userhhha"}, {"rating": 4, "comment": "Itchy tulle on skin.", "session": "useriiia"}]},
    {"product_index": 32, "reviews": [{"rating": 5, "comment": "Softest maxi ever.", "session": "userjjja"}, {"rating": 5, "comment": "Slits add movement.", "session": "userkkka"}]},
    {"product_index": 33, "reviews": [{"rating": 5, "comment": "Buttons are functional.", "session": "userllla"}, {"rating": 4, "comment": "Light but see-through.", "session": "usermmma"}, {"rating": 5, "comment": "Summer essential.", "session": "usernnna"}]},
    {"product_index": 34, "reviews": [{"rating": 5, "comment": "Shines like a star.", "session": "useroooa"}, {"rating": 5, "comment": "Halter fits great.", "session": "userpppa"}]}
]

def seed_products():
    """Add sample products to the database"""
    print("🌱 Seeding products...")
    created_products = []
    
    for i, product in enumerate(SAMPLE_PRODUCTS, 1):
        try:
            response = requests.post(f"{BASE_URL}/products/", json=product)
            if response.status_code == 200:
                created_product = response.json()
                created_products.append(created_product)
                print(f"✅ [{i}/{len(SAMPLE_PRODUCTS)}] Created: {product['name']}")
            else:
                print(f"❌ Failed to create {product['name']}: {response.status_code}")
        except Exception as e:
            print(f"❌ Error creating {product['name']}: {str(e)}")
    
    return created_products

def seed_reviews(products):
    """Add sample reviews to products"""
    print("\n⭐ Seeding reviews...")
    
    for review_set in SAMPLE_REVIEWS:
        product_idx = review_set['product_index']
        if product_idx >= len(products):
            continue
            
        product = products[product_idx]
        product_id = product['id']
        
        for review in review_set['reviews']:
            try:
                review_data = {
                    "product_id": product_id,
                    "session_id": review['session'],
                    "rating": review['rating'],
                    "comment": review['comment']
                }
                response = requests.post(f"{BASE_URL}/reviews/", json=review_data)
                if response.status_code == 200:
                    print(f"✅ Added review for {product['name']} ({review['rating']}⭐)")
                else:
                    print(f"⚠️  Could not add review: {response.json().get('detail', 'Unknown error')}")
            except Exception as e:
                print(f"❌ Error adding review: {str(e)}")

def seed_reviews_no_product():
    """Add sample reviews to products"""
    print("\n⭐ Seeding reviews...")
    
    for review_set in SAMPLE_REVIEWS:
        product_idx = review_set['product_index']
        # if product_idx >= len(products):
        #     continue
            
        # product = products[product_idx]
        product_id = product_idx
        
        for review in review_set['reviews']:
            try:
                review_data = {
                    "product_id": product_id,
                    "session_id": review['session'],
                    "rating": review['rating'],
                    "comment": review['comment']
                }
                response = requests.post(f"{BASE_URL}/reviews/", json=review_data)
                if response.status_code == 200:
                    print(f"✅ Added review ({review['rating']}⭐)")
                else:
                    print(f"⚠️  Could not add review: {response.json().get('detail', 'Unknown error')}")
            except Exception as e:
                print(f"❌ Error adding review: {str(e)}")

def main():
    print("=" * 60)
    print("🎨 DRESS E-COMMERCE - DATABASE SEEDING SCRIPT")
    print("=" * 60)
    print("\n⚠️  Make sure the backend server is running at http://localhost:8000")
    print("Press Enter to continue or Ctrl+C to cancel...")
    input()
    
    # Test connection
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code != 200:
            print("❌ Backend server is not responding. Please start it first.")
            return
    except Exception as e:
        print(f"❌ Cannot connect to backend server: {str(e)}")
        print("Please start the backend with: uvicorn app.main:app --reload")
        return
    
    print("\n✅ Connected to backend server\n")
    # Seed reviews
    # seed_reviews_no_product()
    
    # Seed products
    products = seed_products()
    
    if products:
        print(f"\n✅ Successfully created {len(products)} products")
        
        # Seed reviews
        seed_reviews(products)
        
        print("\n" + "=" * 60)
        print("✨ SEEDING COMPLETE!")
        print("=" * 60)
        print(f"\n📊 Summary:")
        print(f"   - Products created: {len(products)}")
        print(f"   - Reviews added: {sum(len(r['reviews']) for r in SAMPLE_REVIEWS)}")
        print(f"\n🌐 Visit http://localhost:3000 to see your store!")
        print("=" * 60)
    else:
        print("\n❌ No products were created. Please check the backend logs.")

if __name__ == "__main__":
    main()