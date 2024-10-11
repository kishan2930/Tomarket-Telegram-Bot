import os
import sys
import json
import time
import random
import argparse
import requests
from base64 import b64decode, urlsafe_b64decode
from datetime import datetime
from urllib.parse import parse_qs
from colorama import init, Fore, Style

merah = Fore.LIGHTRED_EX
kuning = Fore.LIGHTYELLOW_EX
hijau = Fore.LIGHTGREEN_EX
biru = Fore.LIGHTBLUE_EX
putih = Fore.LIGHTWHITE_EX
hitam = Fore.LIGHTBLACK_EX
reset = Style.RESET_ALL
line = putih + "~" * 50

# New imports
import asyncio

class Config:
    def __init__(self):
        self.config_file = "config.json"
        self.load_config()

    def load_config(self):
        if not os.path.exists(self.config_file) or os.path.getsize(self.config_file) == 0:
            self.create_default_config()
        else:
            try:
                with open(self.config_file, 'r') as f:
                    self.data = json.load(f)
            except json.JSONDecodeError:
                print(f"{merah}Error reading config file. Creating default configuration.{reset}")
                self.create_default_config()

    def save_config(self):
        with open(self.config_file, 'w') as f:
            json.dump(self.data, f, indent=4, sort_keys=True)

    def create_default_config(self):
        default_config = {
            "interval": 3,
            "auto_complete_task": True,
            "auto_play_game": True,
            "auto_spin": True,
            "game_point": {
                "low": 220,
                "high": 250
            },
            "clow": 2,
            "chigh": 3
        }
        self.data = default_config
        self.save_config()
        print(f"{hijau}Default configuration created.{reset}")

    def toggle_setting(self, setting):
        self.data[setting] = not self.data[setting]
        self.save_config()

    def update_range(self, setting, low, high):
        self.data[setting]["low"] = low
        self.data[setting]["high"] = high
        self.save_config()

    def update_simple_range(self, low_key, high_key, low, high):
        self.data[low_key] = low
        self.data[high_key] = high
        self.save_config()

class Tomartod:
    def __init__(self):
        self.headers = {
            "host": "api-web.tomarket.ai",
            "connection": "keep-alive",
            "accept": "application/json, text/plain, */*",
            "user-agent": "Mozilla/5.0 (Linux; Android 10; Redmi 4A / 5A Build/QQ3A.200805.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/86.0.4240.185 Mobile Safari/537.36",
            "content-type": "application/json",
            "origin": "https://mini-app.tomarket.ai",
            "x-requested-with": "tw.nekomimi.nekogram",
            "sec-fetch-site": "same-site",
            "sec-fetch-mode": "cors",
            "sec-fetch-dest": "empty",
            "referer": "https://mini-app.tomarket.ai/",
            "accept-language": "en-US,en;q=0.9",
        }
        self.marinkitagawa = lambda data: {
            key: value[0] for key, value in parse_qs(data).items()
        }
        self.config = Config()

    def set_proxy(self, proxy=None):
        self.ses = requests.Session()
        if proxy is not None:
            self.ses.proxies.update({"http": proxy, "https": proxy})

    def set_authorization(self, auth):
        self.headers["authorization"] = auth

    def del_authorization(self):
        if "authorization" in self.headers.keys():
            self.headers.pop("authorization")

    def login(self, data):
        url = "https://api-web.tomarket.ai/tomarket-game/v1/user/login"
        data = json.dumps(
            {
                "init_data": data,
                "invite_code": "",
            }
        )
        self.del_authorization()
        res = self.http(url, self.headers, data)
        if res.status_code != 200:
            self.log(f"{merah}failed fetch token authorization, check http.log !")
            return None
        data = res.json().get("data")
        token = data.get("access_token")
        if token is None:
            self.log(f"{merah}failed fetch token authorization, check http.log !")
            return None
        return token

    def start_farming(self):
        data = json.dumps({"game_id": "53b22103-c7ff-413d-bc63-20f6fb806a07"})
        url = "https://api-web.tomarket.ai/tomarket-game/v1/farm/start"
        res = self.http(url, self.headers, data)
        if res.status_code != 200:
            self.log(f"{merah}failed start farming, check http.log last line !")
            return False

        data = res.json().get("data")
        end_farming = data["end_at"]
        format_end_farming = (
            datetime.fromtimestamp(end_farming).isoformat(" ").split(".")[0]
        )
        self.log(f"{hijau}success start farming !")

    def end_farming(self):
        data = json.dumps({"game_id": "53b22103-c7ff-413d-bc63-20f6fb806a07"})
        url = "https://api-web.tomarket.ai/tomarket-game/v1/farm/claim"
        res = self.http(url, self.headers, data)
        if res.status_code != 200:
            self.log(f"{merah}failed start farming, check http.log last line !")
            return False

        poin = res.json()["data"]["claim_this_time"]
        self.log(f"{hijau}success claim farming !")
        self.log(f"{hijau}reward : {putih}{poin}")

    def daily_claim(self):
        url = "https://api-web.tomarket.ai/tomarket-game/v1/daily/claim"
        data = json.dumps({"game_id": "fa873d13-d831-4d6f-8aee-9cff7a1d0db1"})
        res = self.http(url, self.headers, data)
        if res.status_code != 200:
            self.log(f"{merah}failed claim daily sign,check http.log last line !")
            return False

        data = res.json().get("data")
        if isinstance(data, str):
            self.log(f"{kuning}maybe already sign in")
            return

        poin = data.get("today_points")
        self.log(
            f"{hijau}success claim {biru}daily sign {hijau}reward : {putih}{poin} !"
        )
        return

    def play_game_func(self, amount_pass):
        data_game = json.dumps({"game_id": "59bcd12e-04e2-404c-a172-311a0084587d"})
        start_url = "https://api-web.tomarket.ai/tomarket-game/v1/game/play"
        claim_url = "https://api-web.tomarket.ai/tomarket-game/v1/game/claim"
        for i in range(amount_pass):
            res = self.http(start_url, self.headers, data_game)
            if res.status_code != 200:
                self.log(f"{merah}failed start game !")
                return

            self.log(f"{hijau}success {biru}start{hijau} game !")
            self.countdown(30)
            point = random.randint(self.config.data["game_point"]["low"], self.config.data["game_point"]["high"])
            data_claim = json.dumps(
                {"game_id": "59bcd12e-04e2-404c-a172-311a0084587d", "points": point}
            )
            res = self.http(claim_url, self.headers, data_claim)
            if res.status_code != 200:
                self.log(f"{merah}failed claim game point !")
                continue

            self.log(f"{hijau}success {biru}claim{hijau} game point : {putih}{point}")

    def get_balance(self):
        url = "https://api-web.tomarket.ai/tomarket-game/v1/user/balance"
        while True:
            res = self.http(url, self.headers, "")
            if res.status_code != 200:
                self.log(f"{merah}failed fetch balance !")
                continue
            data = res.json().get("data")
            if data is None:
                self.log(f"{merah}failed get data !")
                return None

            timestamp = data["timestamp"]
            balance = data["available_balance"]
            self.log(f"{biru}balance : {putih}{balance}")
            if "daily" not in data.keys():
                self.daily_claim()
                continue

            if data["daily"] is None:
                self.daily_claim()
                continue

            next_daily = data["daily"]["next_check_ts"]
            if timestamp > next_daily:
                self.daily_claim()

            if "farming" not in data.keys():
                self.log(f"{kuning}farming not started !")
                result = self.start_farming()
                continue

            end_farming = data["farming"]["end_at"]
            format_end_farming = (
                datetime.fromtimestamp(end_farming).isoformat(" ").split(".")[0]
            )
            if timestamp > end_farming:
                self.end_farming()
                continue

            self.log(f"{kuning}not time to claim !")
            self.log(f"{kuning}end farming at : {putih}{format_end_farming}")
            
            # Implement task feature
            if self.config.data["auto_complete_task"]:
                self.log(f"{biru}Processing tasks...")
                self.list_tasks()
                # Removed sleep here

            # Implement spin feature
            if self.config.data["auto_spin"]:
                self.log(f"{biru}Checking spin opportunities...")
                self.assets_spin()
                # Removed sleep here
                self.tickets_user()
                # Removed sleep here

            if self.config.data["auto_play_game"]:
                self.log(f"{biru}auto play game is enable !")
                play_pass = data.get("play_passes")
                self.log(f"{biru}game ticket : {putih}{play_pass}")
                if int(play_pass) > 0:
                    self.play_game_func(play_pass)
                    continue

            _next = end_farming - timestamp
            return _next + random.randint(self.config.data["clow"], self.config.data["chigh"])

    def load_data(self, file):
        datas = [i for i in open(file).read().splitlines() if len(i) > 0]
        if len(datas) <= 0:
            print(
                f"{merah}0 account detected from {file}, fill your data in {file} first !{reset}"
            )
            sys.exit()

        return datas

    def save(self, id, token):
        tokens = json.loads(open("tokens.json").read())
        tokens[str(id)] = token
        open("tokens.json", "w").write(json.dumps(tokens, indent=4))

    def get(self, id):
        tokens = json.loads(open("tokens.json").read())
        if str(id) not in tokens.keys():
            return None

        return tokens[str(id)]

    def is_expired(self, token):
        header, payload, sign = token.split(".")
        deload = urlsafe_b64decode(payload + "==").decode()
        jeload = json.loads(deload)
        now = int(datetime.now().timestamp())
        if now > jeload["exp"]:
            return True
        return False

    def http(self, url, headers, data=None):
        while True:
            try:
                now = datetime.now().isoformat(" ").split(".")[0]
                if data is None:
                    res = self.ses.get(url, headers=headers, timeout=100)
                elif data == "":
                    res = self.ses.post(url, headers=headers, timeout=100)
                else:
                    res = self.ses.post(url, headers=headers, data=data, timeout=100)
                open("http.log", "a", encoding="utf-8").write(
                    f"{now} - {res.status_code} - {res.text}\n"
                )
                return res
            except requests.exceptions.ProxyError:
                print(f"{merah}bad proxy !")
                time.sleep(1)

            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
                print(f"{merah}connection error / connection timeout !")
                time.sleep(1)
                continue

    def countdown(self, t):
        for i in range(t, 0, -1):
            menit, detik = divmod(i, 60)
            jam, menit = divmod(menit, 60)
            jam = str(jam).zfill(2)
            menit = str(menit).zfill(2)
            detik = str(detik).zfill(2)
            print(f"{putih}waiting {jam}:{menit}:{detik}     ", flush=True, end="\r")
            time.sleep(1)
        print("                                        ", flush=True, end="\r")

    def log(self, msg):
        now = datetime.now().isoformat(" ").split(".")[0]
        print(f"{hitam}[{now}]{reset} {msg}{reset}")

    def list_tasks(self):
        url = "https://api-web.tomarket.ai/tomarket-game/v1/tasks/list"
        data = json.dumps({"language_code": "en"})
        res = self.http(url, self.headers, data)
        if res.status_code != 200:
            self.log(f"{merah}Failed to fetch tasks, check http.log!")
            return
        tasks_data = res.json().get("data")
        self.process_category(tasks_data)

    def process_category(self, category_data):
        for category in category_data:
            if isinstance(category_data[category], list):
                for task in category_data[category]:
                    self.process_task(task)
            elif isinstance(category_data[category], dict):
                self.process_category(category_data[category])

    def process_task(self, task):
        task_id = task.get('taskId')
        task_title = task.get('title')
        task_status = task.get('status')
        task_score = task.get('score')
        wait_second = task.get('waitSecond', 0)
        
        # New conditions to skip certain tasks
        if (
            ('handleFunc' in task and ('walletAddress' in task['handleFunc'] or 'boost' in task['handleFunc'] or 'checkInvite' in task['handleFunc'])) or
            ('tag' in task and 'classmate' in task['tag']) or
            ('type' in task and 'classmate' in task['type'].lower())
        ):
            self.log(f"{kuning}Skipping task: {task_title} (Unsupported task type)")
            return

        if task_status == 0 and task.get('type') == "mysterious":
            self.claim_tasks(task_id, task_title, task_score)
        elif task_status == 0:
            self.start_tasks(task_id, task_title, wait_second, task_score)
        elif task_status == 1:
            self.check_tasks(task_id, task_title, task_score)
        elif task_status == 2:
            self.claim_tasks(task_id, task_title, task_score)

    def start_tasks(self, task_id, task_title, task_waitsecond, task_score):
        url = "https://api-web.tomarket.ai/tomarket-game/v1/tasks/start"
        data = json.dumps({"task_id": task_id})
        res = self.http(url, self.headers, data)
        if res.status_code != 200:
            self.log(f"{merah}Failed to start task {task_title}, check http.log!")
            return
        start_tasks = res.json()
        if start_tasks['status'] == 0:
            if start_tasks['data']['status'] == 1:
                self.log(f"{biru}Task {task_title} started. Waiting {task_waitsecond} seconds.")
                time.sleep(task_waitsecond)
                self.check_tasks(task_id, task_title, task_score)
            elif start_tasks['data']['status'] == 2:
                self.claim_tasks(task_id, task_title, task_score)

    def check_tasks(self, task_id, task_title, task_score):
        url = "https://api-web.tomarket.ai/tomarket-game/v1/tasks/check"
        data = json.dumps({"task_id": task_id})
        res = self.http(url, self.headers, data)
        if res.status_code != 200:
            self.log(f"{merah}Failed to check task {task_title}, check http.log!")
            return
        check_tasks = res.json()
        if check_tasks['status'] == 0:
            if check_tasks['data']['status'] == 2:
                self.claim_tasks(task_id, task_title, task_score)

    def claim_tasks(self, task_id, task_title, task_score):
        url = "https://api-web.tomarket.ai/tomarket-game/v1/tasks/claim"
        data = json.dumps({"task_id": task_id})
        res = self.http(url, self.headers, data)
        if res.status_code != 200:
            self.log(f"{merah}Failed to claim task {task_title}, check http.log!")
            return
        claim_tasks = res.json()
        if claim_tasks['status'] == 0:
            self.log(f"{hijau}Claimed {task_score} points from task {task_title}")

    def assets_spin(self):
        url = "https://api-web.tomarket.ai/tomarket-game/v1/spin/assets"
        data = json.dumps({"language_code": "en"})
        res = self.http(url, self.headers, data)
        if res.status_code != 200:
            self.log(f"{merah}Failed to fetch spin assets, check http.log!")
            return
        assets_spin = res.json()
        if assets_spin['status'] == 0:
            for balance in assets_spin['data']['balances']:
                if balance['balance_type'] == 'Star':
                    if balance['balance'] == 0:
                        self.log(f"{kuning}You don't have any Tomarket Stars")
                        return
                    return self.raffle_spin(category='tomarket')

    def tickets_user(self):
        url = "https://api-web.tomarket.ai/tomarket-game/v1/user/tickets"
        data = json.dumps({"language_code": "en"})
        res = self.http(url, self.headers, data)
        if res.status_code != 200:
            self.log(f"{merah}Failed to fetch user tickets, check http.log!")
            return
        tickets_user = res.json()
        if tickets_user['status'] == 0:
            while tickets_user['data']['ticket_spin_1'] > 0:
                self.raffle_spin(category='ticket_spin_1')
                time.sleep(random.randint(3, 5))
                tickets_user['data']['ticket_spin_1'] -= 1

    def raffle_spin(self, category):
        url = "https://api-web.tomarket.ai/tomarket-game/v1/spin/raffle"
        data = json.dumps({"category": category})
        res = self.http(url, self.headers, data)
        if res.status_code != 200:
            self.log(f"{merah}Failed to perform raffle spin, check http.log!")
            return
        raffle_spin = res.json()
        if raffle_spin['status'] == 0:
            for result in raffle_spin['data']['results']:
                self.log(f"{hijau}You've got {result['amount']} {result['type']} from raffle spin")
        elif raffle_spin['status'] == 400 and raffle_spin['message'] == 'Max 3 spins per day using Tomarket Stars.':
            self.log(f"{kuning}Max 3 spins per day using Tomarket Stars reached")
        elif raffle_spin['status'] == 500 and raffle_spin['message'] == 'Not enough ticket_spin_1 ticket':
            self.log(f"{kuning}Not enough free spin tickets")

    def main(self):
        banner = f"""
{hijau}   ┏━━━┓━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
{biru}   ┃ T ┃o market_ai Auto Claim Bot                     ┃
{hijau}   ┣━━━┫                                               ┃
{biru}   ┃ 0 ┃ By: t.me/KISHAN2930                           ┃
{hijau}   ┣━━━┫ Github: @kishan2930                           ┃
{biru}   ┃ M ┃                                               ┃
{hijau}   ┗━━━┛━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
{hijau}   Message: {putih}Don't Be Evil!
"""
        arg = argparse.ArgumentParser()
        arg.add_argument("--data", default="data.txt")
        arg.add_argument("--config", default="config.json")
        arg.add_argument("--proxy", default="proxies.txt")
        arg.add_argument("--marinkitagawa", action="store_true")
        args = arg.parse_args()
        if not args.marinkitagawa:
            os.system("cls" if os.name == "nt" else "clear")
        print(banner)
        datas = self.load_data(args.data)
        proxies = open(args.proxy).read().splitlines()
        self.log(f"{biru}total account : {putih}{len(datas)}")
        self.log(f"{biru}total proxies detected : {putih}{len(proxies)}")
        use_proxy = True if len(proxies) > 0 else False
        self.log(f"{hijau}use proxy : {putih}{use_proxy}")
        print(line)

        while True:
            print(f"""
{hijau}1. {putih}Start bot
{hijau}2. {putih}Toggle auto complete task ({hijau if self.config.data['auto_complete_task'] else merah}{'ON' if self.config.data['auto_complete_task'] else 'OFF'}{putih})
{hijau}3. {putih}Toggle auto play game ({hijau if self.config.data['auto_play_game'] else merah}{'ON' if self.config.data['auto_play_game'] else 'OFF'}{putih})
{hijau}4. {putih}Set game point range (Current: {self.config.data['game_point']['low']}-{self.config.data['game_point']['high']})
{hijau}5. {putih}Toggle auto spin ({hijau if self.config.data['auto_spin'] else merah}{'ON' if self.config.data['auto_spin'] else 'OFF'}{putih})
{hijau}6. {putih}Set wait time range (Current: {self.config.data['clow']}-{self.config.data['chigh']})
{hijau}7. {putih}Exit
            """)

            choice = input(f"{hijau}Enter your choice: {putih}")

            if choice == '1':
                self.start_bot(datas, proxies, use_proxy)
            elif choice == '2':
                self.config.toggle_setting('auto_complete_task')
                print(f"{hijau}Auto complete task toggled to {self.config.data['auto_complete_task']}")
            elif choice == '3':
                self.config.toggle_setting('auto_play_game')
                print(f"{hijau}Auto play game toggled to {self.config.data['auto_play_game']}")
            elif choice == '4':
                low = int(input(f"{hijau}Enter low game point: {putih}"))
                high = int(input(f"{hijau}Enter high game point: {putih}"))
                self.config.update_range('game_point', low, high)
                print(f"{hijau}Game point range updated to {low}-{high}")
            elif choice == '5':
                self.config.toggle_setting('auto_spin')
                print(f"{hijau}Auto spin toggled to {self.config.data['auto_spin']}")
            elif choice == '6':
                clow = int(input(f"{hijau}Enter low wait time: {putih}"))
                chigh = int(input(f"{hijau}Enter high wait time: {putih}"))
                self.config.update_simple_range('clow', 'chigh', clow, chigh)
                print(f"{hijau}Wait time range updated to {clow}-{chigh}")
            elif choice == '7':
                print(f"{hijau}Exiting...")
                break
            else:
                print(f"{merah}Invalid choice. Please try again.")

            input(f"{biru}Press Enter to continue...")
            os.system("cls" if os.name == "nt" else "clear")
            print(banner)

    def start_bot(self, datas, proxies, use_proxy):
        while True:
            list_countdown = []
            _start = int(time.time())
            for no, data in enumerate(datas):
                if use_proxy:
                    proxy = proxies[no % len(proxies)]
                self.set_proxy(proxy if use_proxy else None)
                parser = self.marinkitagawa(data)
                user = json.loads(parser["user"])
                id = user["id"]
                self.log(
                    f"{biru}account number : {putih}{no+1}{biru}/{putih}{len(datas)}"
                )
                self.log(f"{biru}name : {putih}{user['first_name']}")
                token = self.get(id)
                if token is None:
                    token = self.login(data)
                    if token is None:
                        continue
                    self.save(id, token)

                if self.is_expired(token):
                    token = self.login(data)
                    if token is None:
                        continue
                    self.save(id, token)
                self.set_authorization(token)
                result = self.get_balance()
                print(line)
                self.countdown(self.config.data["interval"])
                list_countdown.append(result)
            _end = int(time.time())
            _tot = _end - _start
            _min = min(list_countdown) - _tot
            if _min > 0:
                self.countdown(_min)

if __name__ == "__main__":
    try:
        app = Tomartod()
        app.main()
    except KeyboardInterrupt:
        sys.exit()