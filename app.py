# app.py
# LibraNet Streamlit app with fines, audiobook fees, previews, big catalog

import streamlit as st
import json, os, random, base64
from datetime import datetime, timedelta
import pandas as pd

DATA_FILE = "library_data.json"
PREVIEW_FOLDER = "previews"
FINE_RATE_PER_DAY = 10
AUDIOBOOK_FEE_PER_DAY = 50
MIN_BORROW_DAYS = 1
MAX_BORROW_DAYS = 7

# ----------------------------
# Helpers
# ----------------------------
def now_iso(): return datetime.now().isoformat()
def from_iso(dt): return datetime.fromisoformat(dt) if dt else None

def make_dummy_mp3_bytes(): return b"ID3\x03\x00\x00\x00\x00\x00\x0fTIT2\x00\x00\x00\x05\x00\x00hey"
def load_mp3_preview(filename: str):
    path = os.path.join(PREVIEW_FOLDER, filename)
    if os.path.exists(path):
        with open(path,"rb") as f: return f.read()
    return make_dummy_mp3_bytes()

def save_data(data): 
    with open(DATA_FILE,"w",encoding="utf-8") as f: json.dump(data,f,indent=2,default=str)
def load_data():
    if not os.path.exists(DATA_FILE): return {"users":{},"items":{}}
    with open(DATA_FILE,"r",encoding="utf-8") as f: return json.load(f)

def generate_id(existing,digits=6):
    while True:
        val=random.randint(10**(digits-1),10**digits-1)
        if val not in existing: return val

# ----------------------------
# Library Manager
# ----------------------------
class LibraryManager:
    def __init__(self):
        raw = load_data()
        self.users = {int(k): v for k,v in raw.get("users",{}).items()}
        for u in self.users.values():
            if "fine_due" not in u: u["fine_due"] = 0
        self.items = {int(k): v for k,v in raw.get("items",{}).items()}
        self.cleanup_expired_audiobooks()
        self._persist()

    def _persist(self): save_data({"users":self.users,"items":self.items})

    # User
    def register_user(self,name,addr,mob):
        uid = generate_id(self.users.keys(),6)
        u = {"user_id":uid,"name":name,"address":addr,"mobile":mob,
             "borrowed_items":[],"subscriptions":[],"history":[],"fine_due":0}
        self.users[uid]=u; self._persist(); return u
    def get_user(self,uid): return self.users.get(uid)

    # Items
    def add_item(self,title,author,cat,preview=None):
        iid=generate_id(self.items.keys(),4)
        self.items[iid]={"item_id":iid,"title":title,"author":author,"category":cat,
                         "available":True,"borrowed_by":None,"borrow_date":None,"return_date":None,
                         "preview_b64": base64.b64encode(preview).decode() if preview and cat=="Audiobook" else None}
        self._persist(); return self.items[iid]
    def find_items(self,cat=None,q=""):
        q=q.lower().strip()
        return [it for it in self.items.values()
                if (not cat or it["category"].lower()==cat.lower())
                and (not q or q in it["title"].lower() or q in it["author"].lower())]

    # Audiobook expiry cleanup
    def cleanup_expired_audiobooks(self):
        now=datetime.now()
        for it in self.items.values():
            if it["category"]=="Audiobook" and it["borrowed_by"]:
                rt=from_iso(it["return_date"])
                if rt and now>rt:
                    uid=it["borrowed_by"]
                    u=self.users.get(uid)
                    if u and it["item_id"] in u["borrowed_items"]:
                        u["borrowed_items"].remove(it["item_id"])
                        u["history"].append({"Date":now_iso(),"Action":"Audiobook expired",
                                             "Item":it["title"],"Category":"Audiobook",
                                             "Details":f"Expired {rt.date()}"})
                    it.update({"available":True,"borrowed_by":None,"borrow_date":None,"return_date":None})
        self._persist()

    # Borrow
    def borrow_item(self,uid,iid,days):
        if not (MIN_BORROW_DAYS<=days<=MAX_BORROW_DAYS): raise ValueError("Days 1–7")
        u=self.get_user(uid); it=self.items[iid]
        self.cleanup_expired_audiobooks()
        if not it["available"]: raise ValueError("Not available")
        bd,rd=datetime.now(),datetime.now()+timedelta(days=days)
        it.update({"available":False,"borrowed_by":uid,"borrow_date":bd.isoformat(),"return_date":rd.isoformat()})
        if it["category"]=="Audiobook":
            fee=days*AUDIOBOOK_FEE_PER_DAY
            u["history"].append({"Date":bd.isoformat(),"Action":"Rented","Item":it["title"],
                                 "Category":"Audiobook","Details":f"Paid Rs{fee}, due {rd.date()}"})
        else:
            u["history"].append({"Date":bd.isoformat(),"Action":"Borrowed","Item":it["title"],
                                 "Category":it["category"],"Details":f"Due {rd.date()}"})
        u["borrowed_items"].append(iid); self._persist(); return rd

    # Return
    def calc_fine(self,iid):
        it=self.items[iid]; rt=from_iso(it["return_date"])
        if not rt: return 0
        delay=(datetime.now()-rt).days
        return FINE_RATE_PER_DAY*delay if delay>0 else 0
    def return_item(self,uid,iid,pay=True):
        u=self.get_user(uid); it=self.items[iid]
        fine=self.calc_fine(iid)
        if fine>0 and not pay: u["fine_due"]+=fine
        u["history"].append({"Date":now_iso(),"Action":"Returned","Item":it["title"],
                             "Category":it["category"],
                             "Details":f"{'Fine Rs'+str(fine) if fine else 'No fine'}"})
        it.update({"available":True,"borrowed_by":None,"borrow_date":None,"return_date":None})
        if iid in u["borrowed_items"]: u["borrowed_items"].remove(iid)
        self._persist(); return fine

    # Fines
    def clear_fines(self,uid):
        u=self.get_user(uid); amt=u["fine_due"]; u["fine_due"]=0
        u["history"].append({"Date":now_iso(),"Action":"Paid fines","Item":"","Category":"Payment","Details":f"Cleared Rs{amt}"})
        self._persist(); return amt

    # Subscription
    def subscribe(self,uid,name,freq):
        u=self.get_user(uid)
        if any(s[0]==name for s in u["subscriptions"]): raise ValueError("Already subscribed")
        u["subscriptions"].append([name,freq])
        u["history"].append({"Date":now_iso(),"Action":"Subscribed","Item":name,
                             "Category":"Subscription","Details":freq})
        self._persist()

    def get_preview(self,iid):
        b64=self.items[iid].get("preview_b64")
        return base64.b64decode(b64) if b64 else make_dummy_mp3_bytes()

# ----------------------------
# Seed big catalog
# ----------------------------
def seed(lm:LibraryManager):
    if lm.items: return
    # 100 books (10 base × 10 volumes)
    base_books=[("Pride and Prejudice","Jane Austen"),("Moby-Dick","Herman Melville"),
           ("War and Peace","Leo Tolstoy"),("The Great Gatsby","F. Scott Fitzgerald"),
           ("Crime and Punishment","Fyodor Dostoevsky"),("The Hobbit","J.R.R. Tolkien"),
           ("Meditations","Marcus Aurelius"),("Man’s Search for Meaning","Viktor Frankl"),
           ("Clean Code","Robert C. Martin"),("Introduction to Algorithms","Cormen")]
    for i in range(1,11):
        for t,a in base_books:
            lm.add_item(f"{t} Vol.{i}",a,"Book")

    # 3 audiobooks
    audios=[("Becoming (Audiobook)","Michelle Obama","becoming.mp3"),
            ("The Alchemist (Audiobook)","Paulo Coelho","alchemist.mp3"),
            ("Sapiens (Audiobook)","Yuval Noah Harari","sapiens.mp3")]
    for t,a,f in audios: lm.add_item(t,a,"Audiobook",preview=load_mp3_preview(f))

    # 5 magazines/newspapers
    for m in ["National Geographic","Forbes","Time","The Hindu","The New York Times"]:
        lm.add_item(m,"Various","Magazine")

# ----------------------------
# Streamlit UI
# ----------------------------
def main():
    st.set_page_config(page_title="LibraNet",page_icon="📚")
    st.title("📚 LibraNet")
    if "lm" not in st.session_state:
        st.session_state.lm=LibraryManager(); seed(st.session_state.lm)
    lm=st.session_state.lm

    st.sidebar.title("Account")
    choice=st.sidebar.radio("Action",["Login","Register","Logout"])
    if choice=="Register":
        n=st.sidebar.text_input("Name"); a=st.sidebar.text_area("Address"); m=st.sidebar.text_input("Mobile")
        if st.sidebar.button("Register"): 
            u=lm.register_user(n,a,m); st.session_state.uid=u["user_id"]; st.sidebar.success(f"UID {u['user_id']}")
    elif choice=="Login":
        uid=st.sidebar.text_input("User ID"); nm=st.sidebar.text_input("Name")
        if st.sidebar.button("Login"):
            try: u=lm.get_user(int(uid))
            except: st.sidebar.error("Invalid ID"); return
            if u and u["name"].lower()==nm.lower():
                st.session_state.uid=int(uid); st.sidebar.success(f"Welcome {u['name']}")
            else: st.sidebar.error("Name mismatch")
    else:
        if st.sidebar.button("Logout"): st.session_state.pop("uid",None)

    uid=st.session_state.get("uid")
    if not uid: st.info("Login or register to continue"); return
    u=lm.get_user(uid); st.subheader(f"Hello {u['name']} (ID {uid})")
    st.write(f"Outstanding fines: Rs {u.get('fine_due',0)}")
    if u.get('fine_due',0)>0 and st.button("Pay all fines"):
        amt=lm.clear_fines(uid); st.success(f"Paid Rs{amt}")

    tabs=st.tabs(["Borrow","Return","Search","Subscriptions","History"])

    # Borrow
    with tabs[0]:
        cat=st.selectbox("Category",["Book","Audiobook","Magazine"])
        q=st.text_input("Search")
        items=[it for it in lm.find_items(cat,q) if it["available"]]
        if items:
            opt=[f"{it['item_id']} - {it['title']} by {it['author']}" for it in items]
            ch=st.selectbox("Choose",opt)
            iid=int(ch.split(" - ")[0])
            days=st.slider("Days",1,7,1)
            if st.button("Borrow"):
                try: rd=lm.borrow_item(uid,iid,days); st.success(f"Due {rd.date()}")
                except Exception as e: st.error(str(e))
        else: st.info("No items available")

    # Return
    with tabs[1]:
        items=[lm.items[i] for i in u["borrowed_items"]]
        if items:
            opt=[f"{it['item_id']} - {it['title']}" for it in items]
            ch=st.selectbox("Borrowed",opt)
            iid=int(ch.split(" - ")[0])
            fine=lm.calc_fine(iid)
            if fine>0: st.warning(f"Fine Rs{fine}")
            if st.button("Return"):
                f=lm.return_item(uid,iid,pay=True); st.success(f"Returned, fine {f}")
        else: st.info("No borrowed items")

    # Search
    with tabs[2]:
        cat=st.selectbox("Type",["Any","Book","Audiobook","Magazine"])
        q=st.text_input("Query")
        res=lm.find_items(None if cat=="Any" else cat,q)
        if res:
            st.dataframe(pd.DataFrame([{"ID":it["item_id"],"Title":it["title"],"Author":it["author"],
                                        "Cat":it["category"],"Avail":"Yes" if it["available"] else "No"} for it in res]))
            auds=[it for it in res if it["category"]=="Audiobook"]
            if auds:
                ch=st.selectbox("Preview audiobook",[f"{it['item_id']} - {it['title']}" for it in auds])
                iid=int(ch.split(" - ")[0]); st.audio(lm.get_preview(iid),format="audio/mp3")
        else: st.info("Nothing found")

    # Subs
    with tabs[3]:
        sub=st.selectbox("Subscription",["National Geographic","Forbes","Time","The Hindu","The New York Times"])
        freq=st.selectbox("Frequency",["Daily","Weekly","Monthly"])
        if st.button("Subscribe"):
            try: lm.subscribe(uid,sub,freq); st.success("Subscribed")
            except Exception as e: st.error(str(e))

    # History
    with tabs[4]:
        hist=pd.DataFrame(u["history"])
        if hist.empty: st.info("No history")
        else:
            hist["Date"]=pd.to_datetime(hist["Date"],errors="coerce")
            st.dataframe(hist.sort_values("Date",ascending=False).dropna(),use_container_width=True)

if __name__=="__main__": main()
