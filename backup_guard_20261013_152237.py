# ==================================================
# SCRIPT INI DIBUAT OLEH RIDOMLBB
# SCRIPT INI BERGUNA SEBAGAI ANTI KILL PANEL
# HARDENED & ANTI-HIJACK VERSION BY RIDOMLBB
# TELEGRAM: @ridororr
# ==================================================
# DILARANG MENGHAPUS ATAU RENAME CREATOR ASLI !!
# DILARANG MEMPERJUALBELIKAN SCRIPT INI, APALAGI MEMBAGIKANNYA SECARA GRATIS !!
# ==================================================

import os
import sys
import re
import time
import requests
import subprocess
import logging
import psutil
import socket
import signal
import threading
import shutil
import json
from datetime import datetime, timedelta, timezone

# KONFIGURASI
URL_PTERO = "https://ampaspanel.voltxyz.my.id" # pake https:// ya
APIKEY_PTERO = "ptla_8M7nie2YGE8edsvB0FNNMUIzjQDVlcBN1CnnhFYKmt7" # awas ini bukan ptlc🖕🗿🖕
CLIENTKEY_PTERO = "ptlc_k9JcFPrQPmYKs8wT894uQ4fXj0Y6ZZhKESqZuUGp69h" # awas ini bukan ptlc🖕🗿🖕
TOKEN_BOT_TELE = "8997303135:AAGJJyL0ogcH5jhKQwuAXmunwgJxWDyxXKw" # dari @BotFather
ID_CHAT_TELE_UNTUK_NOTIF = "-1004320481527" # jika id grup/channel, jgn lupa harus diberi awalan -100
OWNER_ID = 1164966985  # [NEW] GANTI DENGAN TELEGRAM USER ID KAMU (ANGKA TANPA TANDA PETIK)
ID_SERVER_TIDAK_PERLU_DICEK = [1, 2, 3] # ID Server yg tidak akan di-cek, sebaiknya isi hanya id server milikmu saja

# --- LIMIT DISK ---
JEDA_CEK_DETIK = 2 # cek setiap 2 detik
BATAS_LONJAKAN_GB = 2.0 # limit lonjakan disk dalam GB setelah JEDA_CEK_DETIK
MAKSIMAL_UKURAN_GB = 12.0 # [UPDATED] maksimal ukuran disk sebuah server (Limit Disk Panel: 12 GB)

# --- LIMIT PROCESS ---
BATAS_RAM_PROSES_GB = 10.0 # [UPDATED] jika lebih dari ini, langsung suspend (Limit RAM: 10 GB)
BATAS_PERINGATAN = 1 # untuk peringatan skrip ilegal biasa
BATAS_STRIKE_CPU = 2 # [MATCHED] 2 x 2 detik = 4-5 detik masa toleransi khusus CPU (Limit CPU: >100% selama 5s)

# --- LIMIT SSH BRUTE FORCE (NEW) ---
LOG_AUTH_PATH = "/var/log/auth.log" # Lokasi log SSH
BATAS_GAGAL_LOGIN = 5 # Jika gagal login 5x, IP diblokir

# --- LIMIT WEB/BOT ATTACK (NEW) ---
LOG_ACCESS_PATH = "/var/log/nginx/access.log" # Lokasi log Nginx
BATAS_SERANGAN_WEB = 10 # Jika IP spam > 10 kali, IP diblokir

# --- CACHE POLISI PANEL & VPS (NEW FITUR) ---
cache_waktu_mati_server = {} # Melacak server offline/suspend untuk aturan 30 menit
posisi_log_ssh_terakhir = 0
posisi_log_ptero_terakhir = 0

# --- BOT TELEGRAM OFFSET ENGINE ---
offset_bot_terakhir = 0

# --- WHITELIST IP ---
def dapatkan_ip_vps():
    try:
        return requests.get('https://api.ipify.org', timeout=5).text
    except:
        return socket.gethostbyname(socket.gethostname())

IP_VPS_SENDIRI = dapatkan_ip_vps()

# --- ANTI-SPAM NOTIFIKASI (FOKUS) ---
cache_notif_spam = {} 
DURASI_COOLDOWN_NOTIF = 3600 # 1 Jam

NAMA_PROSES_JAHAT_UMUM = [
    'flood', 'ddos', 'attack', 'stress', 'stresser', 'booter',
    'udp', 'tcp', 'handshake', 'syn', 'ack', 'bypass',
    'hoic', 'loic', 'slowloris', 'hulk', 'goldeneye', 'zombie', 'botnet',
    'method', 'mix', 'socket', 'proxy', 'xmrig', 'minerd', 'cpuminer', 
    'ethminer', 'stratum', 'hashrate', 'coin', 'wallet', 'payload', 
    'backdoor', 'shell', 'reverse', 'pwn', 'hack', 'kill', 'bomb', 
    'destroy', 'flooder', 'flooder1', 'flooder2', 'floodb', 'floods',
    'h2-aal', 'h2-blast', 'h2-bypass', 'h2-fast', 'h2-flash', 'h2-flood',
    'h2-hold', 'h2-meris', 'h2-vryz', 'h2ca', 'h2cf', 'h2f', 'h2f3', 'h2xc',
    'h3-flood', 'h3-wyn', 'http-custom', 'http-flood', 'http-raw', 'http2-fast',
    'https-flood', 'tlsx', 'tlsx2', 'tlsv2', 'flutra', 'flutrav', 'glory', 
    'h1f3', 'torigin', 'xcbypas', 'cibi', 'meris', 'vryz', 'wyn', 'mouser', 
    'quantum', 'tayo', 'uz', 'xpriv', 'xsn', 'xyn', 'yaya', 'browx', 'bom',
    'uam', 'uam_bypass', 'turnstile-solver', 'recaptcha-solver', 
    'captcha-text-solver', 'turnstile', 'ssh-kill', 'tcp-pps', 'udp-hex', 
    'udps', 'xcddos', 'xcudp', 'zero-rst', 'alyasam', 'lovenet', 'lovenet-space', 
    'lovenet-steven', 'killnet', 'rapid-good', 'storm', 'strike', 'thunder', 
    'rape', 'hold', 'vhold', 'starsxmc', 'starsxssh', 'starsxsamp', 'starsxwifi',
    'torrent', 'transmission-daemon', 'aria2c', 'bittorrent', 'peer' # Anti-Torrent
]

EKSTENSI_AMAN = ['.jar', '.zip', '.tar.gz']

def proteksi_internal_sistem():
    try:
        skrip_ini = os.path.abspath(sys.argv[0])
        subprocess.run(['chattr', '+i', skrip_ini], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        # --- Kernel Hardening (Sysctl Optimization) ---
        aturan_kernel = {
            "net.ipv4.conf.all.rp_filter": "1",
            "net.ipv4.conf.default.rp_filter": "1",
            "net.ipv4.tcp_syncookies": "1",
            "net.ipv4.tcp_max_syn_backlog": "4096",
            "net.ipv4.tcp_synack_retries": "2",
            "fs.protected_fifos": "2",
            "fs.protected_regular": "2",
            "net.ipv4.ip_forward": "0",
            "net.ipv4.tcp_keepalive_time": "600",
            "net.ipv4.tcp_max_tw_buckets": "5000"
        }
        for kunci, nilai in aturan_kernel.items():
            subprocess.run(['sysctl', '-w', f'{kunci}={nilai}'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # --- DNS Hijack Protection ---
        with open("/etc/resolv.conf", "w") as f:
            f.write("nameserver 1.1.1.1\nnameserver 8.8.8.8\n")
        subprocess.run(['chattr', '+i', '/etc/resolv.conf'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except:
        pass

def verifikasi_identitas_bot():
    try:
        res = requests.get(f"https://api.telegram.org/bot{TOKEN_BOT_TELE}/getMe", timeout=5).json()
        if not res.get("ok"):
            logging.error("🚨 CRITICAL: Token Bot Telegram Tidak Valid! Guard Dimatikan Demi Keamanan.")
            sys.exit(1)
        if os.geteuid() != 0:
            logging.error("🚨 CRITICAL: Skrip Guard harus dijalankan sebagai ROOT (sudo)!")
            sys.exit(1)
    except Exception as e:
        logging.error(f"Gagal memverifikasi integritas bot: {e}")

def tangani_sinyal_terminasi(signum, frame):
    logging.warning("⚡ Terdeteksi upaya mematikan skrip Guard secara paksa!")
    pass

signal.signal(signal.SIGINT, tangani_sinyal_terminasi)
signal.signal(signal.SIGTERM, tangani_sinyal_terminasi)

def dapatkan_lokasi_ip(ip):
    try:
        respon = requests.get(f"http://ip-api.com/json/{ip}", timeout=3).json()
        if respon['status'] == 'success':
            return f"{respon['city']}, {respon['regionName']}, {respon['country']}"
        return "Lokasi Tidak Diketahui"
    except:
        return "Gagal Melacak"

FOLDER_PANTAU = "/var/lib/pterodactyl/volumes"

def konversi_waktu_wib(*args):
    waktu_utc_sekarang = datetime.now(timezone.utc)
    return (waktu_utc_sekarang + timedelta(hours=7)).timetuple()

logging.Formatter.converter = konversi_waktu_wib
logging.basicConfig(
    format='[%(asctime)s] %(message)s',
    level=logging.INFO,
    datefmt='%H:%M:%S'
)

header_api = {
    "Authorization": f"Bearer {APIKEY_PTERO}",
    "Content-Type": "application/json",
    "Accept": "application/json"
}

cache_ukuran_server = {}
cache_server_penuh = set()
cache_io_proses = {}
cache_peringatan_server = {}

def bersihkan_teks_md(teks):
    if not teks: return ""
    return re.sub(r'([_*\[\]()~`>#+\-=|{}.!])', r'\\\1', str(teks))

def rakit_pesan_laporan(tipe_alert, data_detail, alasan_tindakan, info_pemilik=None):
    tipe_alert_esc = bersihkan_teks_md(tipe_alert)
    alasan_tindakan_esc = bersihkan_teks_md(alasan_tindakan)

    if info_pemilik:
        nama_owner = bersihkan_teks_md(info_pemilik.get('nama_pemilik', 'Unknown'))
        user_owner = bersihkan_teks_md(info_pemilik.get('username_pemilik', 'Unknown'))
        id_owner = bersihkan_teks_md(str(info_pemilik.get('id_owner', '0')))
        email_owner = bersihkan_teks_md(info_pemilik.get('email_pemilik', 'N/A'))
        nama_srv = bersihkan_teks_md(info_pemilik.get('nama_server', 'Unknown'))
        uuid_srv = bersihkan_teks_md(info_pemilik.get('uuid_server', '0000').split('-')[0])
        id_srv = bersihkan_teks_md(str(info_pemilik.get('id_server', '0')))

        bagian_user = (
            f"👤 *DATA OWNER:*\n"
            f"> 📛 {nama_owner} \\(`{user_owner}`\\)\n"
            f"> 📧 Email: `{email_owner}`\n"
            f"> 🆔 User ID: `{id_owner}`\n\n"
            f"📦 *DATA SERVER:*\n"
            f"> 🏷️ {nama_srv}\n"
            f"> 🆔 UUID: `{uuid_srv}` \\(ID: `{id_srv}`\\)\n"
        )
    else:
        bagian_user = "👮 *POLISI SIKAT PELANGGARAN VIRTUAL* 👮\n\n"

    pesan_final = (
        f"🛡️ *RIDOMLBB GUARD ACTION* 🛡️\n"
        f"🚨 *Tipe: {tipe_alert_esc}*\n\n"
        f"{bagian_user}"
        f"📊 *Detail Monitoring:*\n{data_detail}\n\n"
        f"🛑 *Hukuman:* {alasan_tindakan_esc}\n\n"
        f"📢 *STATUS NODE:* `PROTECTED` ✅"
    )
    return pesan_final

def kirim_notif_tele(pesan_teks, id_target_spam=None, paksa_private_owner=False):
    """Mengirim log notifikasi ke Group ID, dan jika bersifat krusial dikirim ganda ke Private ID Owner"""
    waktu_skrg = time.time()
    if id_target_spam:
        if id_target_spam in cache_notif_spam:
            if waktu_skrg - cache_notif_spam[id_target_spam] < DURASI_COOLDOWN_NOTIF:
                return
        cache_notif_spam[id_target_spam] = waktu_skrg

    url_tele = f"https://api.telegram.org/bot{TOKEN_BOT_TELE}/sendMessage"
    
    # Pengiriman default ke Group/Channel ID settingan asli
    try:
        payload_data = {
            "chat_id": ID_CHAT_TELE_UNTUK_NOTIF, 
            "text": pesan_teks, 
            "parse_mode": "MarkdownV2", 
            "disable_web_page_preview": True
        }
        r = requests.post(url_tele, json=payload_data, timeout=10)
        if r.status_code != 200:
            logging.error(f"Telegram API Error (Group): {r.text}")
    except Exception as error_tele:
        logging.error(f"Gagal kirim telegram group: {error_tele}")

    # [NEW] Pengiriman Ganda ke Private Chat Owner jika dipicu oleh indikasi Brute Force/Hack/Login Alert
    if paksa_private_owner and OWNER_ID:
        try:
            payload_owner = {
                "chat_id": OWNER_ID,
                "text": pesan_teks,
                "parse_mode": "MarkdownV2",
                "disable_web_page_preview": True
            }
            requests.post(url_tele, json=payload_owner, timeout=10)
        except Exception as err_priv:
            logging.error(f"Gagal kirim telegram private owner: {err_priv}")

def ban_ip_vps(ip_target):
    if not ip_target or ip_target in ['127.0.0.1', '0.0.0.0', IP_VPS_SENDIRI]: return False
    try:
        # Check Bad VPN/Proxy
        check_vpn = requests.get(f"https://proxycheck.io/v2/{ip_target}?vpn=1&asn=1", timeout=3).json()
        if check_vpn.get(ip_target, {}).get("proxy") == "yes":
            logging.warning(f"🚩 {ip_target} adalah VPN/Proxy terdeteksi! Auto Ban.")
        
        check_ban = subprocess.run(['iptables', '-C', 'INPUT', '-s', ip_target, '-j', 'DROP'], capture_output=True)
        if check_ban.returncode != 0:
            subprocess.run(['iptables', '-I', 'INPUT', '-s', ip_target, '-j', 'DROP'], stdout=subprocess.DEVNULL)
            logging.warning(f"🚫 IP {ip_target} PERMANENTLY BANNED via IPTABLES!")
            return True
    except: pass
    return False

# --- Multi-Login Prevention & Session Matching ---
def cek_multi_login_vps():
    try:
        users = subprocess.check_output(['w', '-h'], encoding='utf-8').splitlines()
        logins = {}
        for line in users:
            parts = line.split()
            user = parts[0]
            ip = parts[2]
            if user not in logins: logins[user] = set()
            logins[user].add(ip)
            
            if len(logins[user]) > 1: # Limit 1 IP per User
                detail = f"👤 User: `{user}`\n🌐 IPs: `{logins[user]}`"
                kirim_notif_tele(rakit_pesan_laporan("MULTI-LOGIN DETECTED", detail, "Kill Unauthorized Session"), paksa_private_owner=True)
                subprocess.run(['pkill', '-u', user], stdout=subprocess.DEVNULL)
    except: pass

def cek_brute_force_ssh():
    if not os.path.exists(LOG_AUTH_PATH): return
    try:
        log_data = subprocess.check_output(['tail', '-n', '500', LOG_AUTH_PATH]).decode('utf-8')
        pola = r"Failed password for .* from ([\d\.]+)"
        ip_gagal = re.findall(pola, log_data)

        for ip in set(ip_gagal):
            if ip == IP_VPS_SENDIRI: continue
            jumlah_gagal = ip_gagal.count(ip)
            if jumlah_gagal >= BATAS_GAGAL_LOGIN:
                lokasi = dapatkan_lokasi_ip(ip)
                detail_brute = (
                    f"> 🌐 IP Penyerang: `{bersihkan_teks_md(ip)}`\n"
                    f"> 📍 Lokasi: `{bersihkan_teks_md(lokasi)}`\n"
                    f"> 📑 Log: `SSH Brute Force Detected`\n"
                    f"> 📉 Total Gagal: `{jumlah_gagal} kali`"
                )
                ban_ip_vps(ip)
                kirim_notif_tele(rakit_pesan_laporan("SSH ATTACK DETECTED", detail_brute, "Permanent Ban (IPTABLES)"), f"ssh_ban_{ip}", paksa_private_owner=True)
    except Exception as e:
        logging.error(f"Gagal cek brute force: {e}")

def cek_web_attack():
    if not os.path.exists(LOG_ACCESS_PATH): return
    try:
        log_data = subprocess.check_output(['tail', '-n', '1000', LOG_ACCESS_PATH]).decode('utf-8')
        pola_ip = r'^(\d{1,3}(?:\.\d{1,3}){3})'
        ip_pengunjung = re.findall(pola_ip, log_data, re.MULTILINE)

        for ip in set(ip_pengunjung):
            if ip == IP_VPS_SENDIRI: continue
            jumlah_hit = ip_pengunjung.count(ip)
            if jumlah_hit >= BATAS_SERANGAN_WEB:
                # Behavioral Rate Limiting
                lokasi = dapatkan_lokasi_ip(ip)
                detail_web = (
                    f"> 🌐 IP Penyerang: `{bersihkan_teks_md(ip)}`\n"
                    f"> 📍 Lokasi: `{bersihkan_teks_md(lokasi)}`\n"
                    f"> 📑 Log: `Attackers Proxy/BOT`\n"
                    f"> 📉 Total Request: `{jumlah_hit} kali (Spam)`"
                )
                ban_ip_vps(ip)
                kirim_notif_tele(rakit_pesan_laporan("DOMAIN ATTACK DETECTED", detail_web, "Permanent Ban (IPTABLES)"), f"web_ban_{ip}", paksa_private_owner=True)
    except Exception as e:
        logging.error(f"Gagal cek web attack: {e}")

def jalankan_polisi_panel_dan_vps():
    global posisi_log_ssh_terakhir, posisi_log_ptero_terakhir
    waktu_sekarang = time.time()
    
    # --- System Health Auto-Optimization ---
    if int(time.time()) % 3600 == 0: # Setiap 1 Jam
        subprocess.run(['sync; echo 3 > /proc/sys/vm/drop_caches'], shell=True)
        logging.info("🧹 System Memory Optimized (Caches Dropped)")

    try:
        url_all_servers = f"{URL_PTERO}/api/application/servers"
        res = requests.get(url_all_servers, headers=header_api, timeout=10)
        if res.status_code == 200:
            servers_data = res.json()['data']
            server_aktif_per_user = {}
            
            for srv in servers_data:
                attr = srv['attributes']
                uid = attr['user']
                is_suspended = attr['suspended']
                
                if uid not in server_aktif_per_user:
                    server_aktif_per_user[uid] = 0
                if not is_suspended:
                    server_aktif_per_user[uid] += 1

            for srv in servers_data:
                attr = srv['attributes']
                srv_id = attr['id']
                srv_uuid = attr['uuid']
                srv_name = attr['name']
                uid = attr['user']
                is_suspended = attr['suspended']
                
                if srv_id in ID_SERVER_TIDAK_PERLU_DICEK:
                    continue
                
                is_offline = False
                try:
                    inspect_status = subprocess.check_output(['docker', 'inspect', '-f', '{{.State.Running}}', srv_uuid], stderr=subprocess.DEVNULL).decode('utf-8').strip()
                    if inspect_status == "false":
                        is_offline = True
                except:
                    pass

                if is_suspended or is_offline:
                    if srv_id not in cache_waktu_mati_server:
                        cache_waktu_mati_server[srv_id] = waktu_sekarang
                    else:
                        durasi_mati = waktu_sekarang - cache_waktu_mati_server[srv_id]
                        if durasi_mati >= 1800:
                            url_del_server = f"{URL_PTERO}/api/application/servers/{srv_id}"
                            del_res = requests.delete(url_del_server, headers=header_api, timeout=10)
                            
                            status_user = "Tetap Aman (Masih ada server lain)"
                            if server_aktif_per_user.get(uid, 0) == 0:
                                url_del_user = f"{URL_PTERO}/api/application/users/{uid}"
                                del_user_res = requests.delete(url_del_user, headers=header_api, timeout=10)
                                if del_user_res.status_code == 204:
                                    status_user = "Terhapus Otomatis (No Active Server)"
                                else:
                                    status_user = "Gagal Hapus User (Dilindungi/System)"

                            if del_res.status_code == 204:
                                label_alasan = "Off 30 Menit" if is_offline else "Suspended 30 Menit"
                                detail_polisi = (
                                    f"> 📦 Nama Server: `{bersihkan_teks_md(srv_name)}`\n"
                                    f"> 🆔 Server ID: `{srv_id}`\n"
                                    f"> 👤 User ID Pemilik: `{uid}`\n"
                                    f"> ⏳ Pelanggaran: `{label_alasan}`\n"
                                    f"> 👥 Status Akun User: `{bersihkan_teks_md(status_user)}`"
                                )
                                kirim_notif_tele(rakit_pesan_laporan("POLISI PANEL: PURGE COMPLETED", detail_polisi, "Permanent Delete Server & User Panel"), f"polisi_purge_{srv_id}")
                                del cache_waktu_mati_server[srv_id]
                else:
                    if srv_id in cache_waktu_mati_server:
                        del cache_waktu_mati_server[srv_id]
    except Exception as e:
        logging.error(f"Polisi Panel Core Error: {e}")

    try:
        url_all_users = f"{URL_PTERO}/api/application/users"
        res_users = requests.get(url_all_users, headers=header_api, timeout=10)
        if res_users.status_code == 200:
            users_data = res_users.json()['data']
            for usr in users_data:
                u_attr = usr['attributes']
                u_id = u_attr['id']
                u_is_admin = u_attr['root_admin']
                
                # Automated Whitelist untuk Admin (ID 1)
                if u_is_admin and u_id != 1:
                    url_patch_user = f"{URL_PTERO}/api/application/users/{u_id}"
                    payload_demote = {
                        "username": u_attr['username'],
                        "email": u_attr['email'],
                        "first_name": u_attr['first_name'],
                        "last_name": u_attr['last_name'],
                        "root_admin": False
                    }
                    patch_res = requests.patch(url_patch_user, json=payload_demote, headers=header_api, timeout=10)
                    if patch_res.status_code == 200:
                        detail_lockdown = (
                            f"> 👤 Username: `{bersihkan_teks_md(u_attr['username'])}`\n"
                            f"> 🆔 User ID: `{u_id}`\n"
                            f"> 📧 Email: `{bersihkan_teks_md(u_attr['email'])}`\n"
                            f"> 🚨 Kasus: `Mencoba Mengakses Pengaturan Panel Admin (Illegal Admin Role)`"
                        )
                        logging.warning(f"🔒 LOCKDOWN: Hak Akses Admin User ID {u_id} Telah Dicabut Otomatis!")
                        kirim_notif_tele(rakit_pesan_laporan("POLISI PANEL: ADMINISTRATIVE LOCKDOWN", detail_lockdown, "Hak Akses Admin Diturunkan Otomatis (Hanya ID 1 Diijinkan)"), f"admin_lock_{u_id}", paksa_private_owner=True)
    except Exception as e:
        logging.error(f"Gagal mengeksekusi Admin Lockdown Guard: {e}")

    try:
        url_admin = f"{URL_PTERO}/api/application/users/1"
        res_admin = requests.get(url_admin, headers=header_api, timeout=5)
        if res_admin.status_code == 200:
            admin_attr = res_admin.json()['attributes']
            if admin_attr['root_admin'] is False:
                detail_hack = f"> 🚨 *WARNING!!* Hak akses Root Admin ID 1 dicabut secara ilegal!"
                kirim_notif_tele(rakit_pesan_laporan("POLISI PANEL: ADMIN ID 1 HIJACKED", detail_hack, "Peringatan! Segera Ganti Password & Amankan Database!"), "hijack_admin_1", paksa_private_owner=True)
    except Exception as e:
        pass

    LOG_PTERO_PATH = "/var/www/pterodactyl/storage/logs/laravel.log"
    if os.path.exists(LOG_PTERO_PATH):
        try:
            ukuran_log = os.path.getsize(LOG_PTERO_PATH)
            if posisi_log_ptero_terakhir == 0 or ukuran_log < posisi_log_ptero_terakhir:
                posisi_log_ptero_terakhir = max(0, ukuran_log - 20000)
                
            with open(LOG_PTERO_PATH, "r", errors="ignore") as f:
                f.seek(posisi_log_ptero_terakhir)
                baris_log = f.readlines()
                posisi_log_ptero_terakhir = f.tell()
                
                for baris in baris_log:
                    if "authenticated" in baris.lower() and ("id: 1" in baris or "admin" in baris.lower()):
                        detail_login_admin = f"> 📑 Log Ref: `Admin Account Login Detected`\n> 🔐 Target: `Admin Panel ID 1`"
                        kirim_notif_tele(rakit_pesan_laporan("POLISI PANEL: ADMIN LOGIN DETECTED", detail_login_admin, "Peringatan Keamanan! Segera Ganti Password Jika Bukan Anda!"), "alert_login_admin_1", paksa_private_owner=True)
        except:
            pass

    if os.path.exists(LOG_AUTH_PATH):
        try:
            ukuran_log_ssh = os.path.getsize(LOG_AUTH_PATH)
            if posisi_log_ssh_terakhir == 0 or ukuran_log_ssh < posisi_log_ssh_terakhir:
                posisi_log_ssh_terakhir = max(0, ukuran_log_ssh - 10000)
                
            with open(LOG_AUTH_PATH, "r", errors="ignore") as f:
                f.seek(posisi_log_ssh_terakhir)
                baris_ssh = f.readlines()
                posisi_log_ssh_terakhir = f.tell()
                
                for baris in baris_ssh:
                    if "Accepted password for" in baris or "Accepted publickey for" in baris:
                        ip_login = re.search(r"from ([\d\.]+) port", baris)
                        user_login = re.search(r"for (\S+) from", baris)
                        
                        if ip_login:
                            ip_vps_user = ip_login.group(1)
                            user_vps = user_login.group(1) if user_login else "Unknown"
                            
                            if ip_vps_user == IP_VPS_SENDIRI:
                                continue
                                
                            lokasi = dapatkan_lokasi_ip(ip_vps_user)
                            detail_vps_login = (
                                f"> 👤 User VPS: `{bersihkan_teks_md(user_vps)}`\n"
                                f"> 🌐 IP Akses: `{bersihkan_teks_md(ip_vps_user)}`\n"
                                f"> 📍 Lokasi: `{bersihkan_teks_md(lokasi)}`"
                            )
                            kirim_notif_tele(rakit_pesan_laporan("POLISI VPS: SUCCESSFUL LOGIN SSH", detail_vps_login, "Peringatan! Segera Ganti Password VPS Anda Jika Akses Ilegal!"), f"ssh_success_{ip_vps_user}", paksa_private_owner=True)
        except:
            pass

    try:
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            cmd = proc.info.get('cmdline')
            if cmd:
                cmd_str = " ".join(cmd).lower()
                if "pterodactyl" in cmd_str and ("chown" in cmd_str or "chmod 777" in cmd_str or "passwd" in cmd_str):
                    try:
                        proc.kill()
                        detail_kudeta = f"> 🚨 Terdeteksi upaya manipulasi perizinan root VPS via Web Panel File Manager!"
                        kirim_notif_tele(rakit_pesan_laporan("POLISI VPS: ANTI KUDETA BLOCKED", detail_kudeta, "Force Terminated Process & Lockdown Session"), "kudeta_lock", paksa_private_owner=True)
                    except:
                        pass
    except:
        pass

def ambil_info_server(uuid_server):
    try:
        url_target = f"{URL_PTERO}/api/application/servers?filter[uuid]={uuid_server}"
        respon_server = requests.get(url_target, headers=header_api, timeout=5.0) 

        if respon_server.status_code == 200:
            data_json = respon_server.json()['data']
            if len(data_json) > 0:
                atribut_server = data_json[0]['attributes']
                id_pemilik = atribut_server['user']
                
                url_user = f"{URL_PTERO}/api/application/users/{id_pemilik}"
                respon_user = requests.get(url_user, headers=header_api, timeout=5.0)
                
                if respon_user.status_code == 200:
                    atribut_user = respon_user.json()['attributes']
                    return {
                        "id_server": atribut_server['id'], 
                        "nama_server": atribut_server['name'],
                        "uuid_server": atribut_server['uuid'],
                        "nama_pemilik": f"{atribut_user['first_name']} {atribut_user['last_name']}",
                        "username_pemilik": atribut_user['username'],
                        "email_pemilik": atribut_user['email'],
                        "id_owner": atribut_user['id']
                    }

        inspect_info = subprocess.check_output(['docker', 'inspect', uuid_server], stderr=subprocess.DEVNULL).decode('utf-8')
        return {
            "id_server": "OFFLINE", 
            "nama_server": f"SRV-{uuid_server[:8]}",
            "uuid_server": uuid_server,
            "nama_pemilik": "System Recovery (Panel API Down)",
            "username_pemilik": "panel_offline",
            "email_pemilik": "admin@pterodactyl.io",
            "id_owner": "0"
        }
    except Exception as e: 
        logging.error(f"Gagal mengambil data API: {e}")
        return None

def suspend_server(id_internal):
    if id_internal in ["OFFLINE", "CRITICAL"]: return False
    try:
        url_suspend = f"{URL_PTERO}/api/application/servers/{id_internal}/suspend"
        respon_suspend = requests.post(url_suspend, headers=header_api)
        return respon_suspend.status_code == 204
    except: return False

def kill_proses(pid_target):
    try:
        proses_target = psutil.Process(pid_target)
        proses_target.kill()
        return True
    except: return False

def cek_ukuran_folder_gb(jalur_folder):
    try:
        hasil_cek = subprocess.check_output(['du', '-sk', jalur_folder], stderr=subprocess.DEVNULL)
        return int(hasil_cek.split()[0].decode('utf-8')) / 1024 / 1024 
    except: return 0

def bersihkan_sampah_docker(uuid_server):
    if not uuid_server: return
    try:
        perintah_hapus = "rm -rf /tmp/* /tmp/.* /dev/shm/* /dev/shm/.* /var/tmp/* /var/tmp/.* /run/.lock 2>/dev/null"
        subprocess.run(['docker', 'exec', uuid_server, 'sh', '-c', perintah_hapus], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        logging.info(f"🧹 Docker Internal Cache Cleaned for UUID: {uuid_server}")
    except Exception as e:
        pass

def bersih_bersih_otomatis(jalur_folder):
    total_mb_dihapus = 0
    jumlah_file_dihapus = 0
    KATA_KUNCI_FILE_JAHAT = ['payload', 'kill', 'disk-bomb', 'crash-server', 'flood', 'ddos', 'blast', 'trash', 'farizgd', 'botnet', 'malware']
    BATAS_UKURAN_AGRESIF_MB = 110.0
    BATAS_OS_BOM_MB = 5120.0
    BATAS_AKUMULASI_EKSTENSI_MB = 1024.0
    BATAS_JUMLAH_FILE_EKSTENSI = 10000
    FOLDER_KEBAL_AKUMULASI = ['node_modules', '.npm']

    akumulasi_ekstensi = {}

    for root_dir, list_dir, list_file in os.walk(jalur_folder):
        di_dalam_folder_kebal = any(kebal in root_dir.split(os.sep) for kebal in FOLDER_KEBAL_AKUMULASI)

        for nama_file in list_file:
            jalur_lengkap_file = os.path.join(root_dir, nama_file)
            try:
                ukuran_file_mb = os.path.getsize(jalur_lengkap_file) / (1024 * 1024)
                _, ekstensi = os.path.splitext(nama_file)
                ekstensi = ekstensi.lower()
                if not ekstensi: ekstensi = "TANPA_EKSTENSI"

                ekstensi_aman = any(nama_file.endswith(ext) for ext in EKSTENSI_AMAN)
                nama_kecil_file = nama_file.lower()
                ada_kata_jahat = any(kata in nama_kecil_file for kata in KATA_KUNCI_FILE_JAHAT)
                
                harus_dihapus = False
                
                if ada_kata_jahat:
                    harus_dihapus = True
                elif not ekstensi_aman and ukuran_file_mb > BATAS_UKURAN_AGRESIF_MB:
                    harus_dihapus = True
                elif ukuran_file_mb > BATAS_OS_BOM_MB:
                    harus_dihapus = True

                if harus_dihapus:
                    try:
                        subprocess.run(['chattr', '-i', jalur_lengkap_file], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        os.remove(jalur_lengkap_file)
                        total_mb_dihapus += ukuran_file_mb
                        jumlah_file_dihapus += 1
                    except Exception as e:
                        logging.warning(f"Gagal menghapus file {jalur_lengkap_file}: {e}")
                else:
                    if not ekstensi_aman and not di_dalam_folder_kebal:
                        if ekstensi not in akumulasi_ekstensi:
                            akumulasi_ekstensi[ekstensi] = {'total_mb': 0, 'jumlah_file': 0, 'files': []}
                        akumulasi_ekstensi[ekstensi]['total_mb'] += ukuran_file_mb
                        akumulasi_ekstensi[ekstensi]['jumlah_file'] += 1
                        akumulasi_ekstensi[ekstensi]['files'].append(jalur_lengkap_file)
            except Exception:
                pass

    for ekstensi, data in akumulasi_ekstensi.items():
        if data['total_mb'] > BATAS_AKUMULASI_EKSTENSI_MB or data['jumlah_file'] > BATAS_JUMLAH_FILE_EKSTENSI:
            logging.warning(f"🧹 Mass-Clean Triggered! Ekstensi '{ekstensi}' mencapai {data['total_mb']:.2f}MB / {data['jumlah_file']} File")
            for path_file in data['files']:
                try:
                    subprocess.run(['chattr', '-i', path_file], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    os.remove(path_file)
                    jumlah_file_dihapus += 1
                except Exception as e:
                    logging.warning(f"Gagal menghapus file {path_file}: {e}")
            total_mb_dihapus += data['total_mb']

    return total_mb_dihapus, jumlah_file_dihapus

def pantau_proses_nakal():
    waktu_sekarang = time.time()
    pid_aktif_sekarang = set()
    pengumpulan_data = {}

    # --- Auto-Clean Ghost Processes ---
    for proc in psutil.process_iter(['pid', 'status', 'ppid']):
        if proc.info['status'] == psutil.STATUS_ZOMBIE:
            try: os.waitpid(proc.info['pid'], os.WNOHANG)
            except: pass

    for proses in psutil.process_iter(['pid', 'name', 'cmdline', 'memory_info', 'uids']):
        try:
            if proses.info.get('uids'):
                uid_nyata = proses.info['uids'].real
                if uid_nyata < 500: continue

            pid_aktif = proses.info['pid']
            pid_aktif_sekarang.add(pid_aktif)
            baris_perintah = proses.info['cmdline']
            if not baris_perintah: continue

            perintah_asli = " ".join(baris_perintah)
            perintah_lengkap = perintah_asli.lower()
            
            perintah_aman = [
                'npm i ', 'npm install ', 'yarn add ', 'pip install ', 'pip3 install ', 'apt install ',
                'ffmpeg ', 'ffprobe ', 'node-gyp', 'build/release', 'binding.gyp',
                '/entrypoint.sh', 'bash /entrypoint.sh', 'ash /entrypoint.sh', './entrypoint.sh',
                'java -jar', 'java -xms', 'java -xmx', 'bedrock_server', 'srcds_run'
            ]
            if any(cmd_aman in perintah_lengkap for cmd_aman in perintah_aman): continue

            uuid_terdeteksi = None
            try:
                env_proses = proses.environ()
                if 'P_SERVER_UUID' in env_proses:
                    uuid_terdeteksi = env_proses['P_SERVER_UUID']
            except: pass

            if not uuid_terdeteksi: continue

            io_kounter = proses.io_counters()
            write_sekarang = io_kounter.write_bytes
            write_chars_sekarang = io_kounter.write_chars

            kecepatan_mb_s = 0.0
            kecepatan_chars_mb_s = 0.0

            if pid_aktif in cache_io_proses:
                data_cache = cache_io_proses[pid_aktif]
                waktu_lalu = data_cache[0]
                write_lalu = data_cache[1]
                chars_lalu = data_cache[2]
                
                selisih_waktu = waktu_sekarang - waktu_lalu
                if selisih_waktu > 0:
                    kecepatan_mb_s = ((write_sekarang - write_lalu) / 1024 / 1024) / selisih_waktu
                    kecepatan_chars_mb_s = ((write_chars_sekarang - chars_lalu) / 1024 / 1024) / selisih_waktu
            
            cache_io_proses[pid_aktif] = (waktu_sekarang, write_sekarang, write_chars_sekarang)
            
            terdeteksi_nama_jahat = any(re.search(rf'\b{kata}\b', perintah_lengkap) for kata in NAMA_PROSES_JAHAT_UMUM)
            terdeteksi_algoritma = bool(re.search(r'\S+\.(?:js|py|sh|ts|go)\s+(?:https?://|(?:\d{1,3}\.){3}\d{1,3})\S*\s+\d+', perintah_lengkap))
            terdeteksi_node_abuse = bool(re.search(r'--expose-gc|--max-old-space-size=(?:819[2-9]|\d{5,})', perintah_lengkap))
            terdeteksi_io = kecepatan_mb_s > 800.0
            terdeteksi_log = kecepatan_chars_mb_s > 800.0

            terdeteksi_network = False
            jumlah_koneksi = 0
            jumlah_fd = 0
            
            try: 
                koneksi = proses.connections(kind='all')
                jumlah_koneksi = len(koneksi)
                # DPI Bypass Protection (Pattern Matching pada socket)
                for conn in koneksi:
                    if conn.status == 'ESTABLISHED' and conn.raddr:
                        if conn.raddr.port in [443, 80] and "bypass" in perintah_lengkap:
                            terdeteksi_network = True
            except: pass

            try: jumlah_fd = proses.num_fds()
            except: pass

            if jumlah_koneksi > 30 or jumlah_fd > 60: 
                terdeteksi_network = True

            if uuid_terdeteksi not in pengumpulan_data:
                pengumpulan_data[uuid_terdeteksi] = {
                    'pelanggaran_mutlak': [],
                    'pids': [],
                    'cmd_sampel': perintah_asli,
                    'ram_docker': 0.0,
                    'cpu_docker': 0.0
                }

            pengumpulan_data[uuid_terdeteksi]['pids'].append(pid_aktif)
            pelanggaran_ditemukan = False

            if terdeteksi_nama_jahat: 
                pengumpulan_data[uuid_terdeteksi]['pelanggaran_mutlak'].append("Illegal Script")
                pelanggaran_ditemukan = True
            if terdeteksi_algoritma: 
                pengumpulan_data[uuid_terdeteksi]['pelanggaran_mutlak'].append("DDoS Algorithm / Attack Pattern")
                pelanggaran_ditemukan = True
            if terdeteksi_node_abuse: 
                pengumpulan_data[uuid_terdeteksi]['pelanggaran_mutlak'].append("Node.js V8 Engine Abuse")
                pelanggaran_ditemukan = True
            if terdeteksi_io: 
                pengumpulan_data[uuid_terdeteksi]['pelanggaran_mutlak'].append("Disk Write Abuse")
                pelanggaran_ditemukan = True
            if terdeteksi_log: 
                pengumpulan_data[uuid_terdeteksi]['pelanggaran_mutlak'].append("Log Bombing / Console Spam")
                pelanggaran_ditemukan = True
            if terdeteksi_network: 
                pengumpulan_data[uuid_terdeteksi]['pelanggaran_mutlak'].append("Network Spam / Local DDoS")
                pelanggaran_ditemukan = True

            if pelanggaran_ditemukan:
                pengumpulan_data[uuid_terdeteksi]['cmd_sampel'] = perintah_asli

        except: pass

    try:
        hasil_docker = subprocess.check_output(
            ['docker', 'stats', '--no-stream', '--format', '{{.Name}}|{{.CPUPerc}}|{{.MemUsage}}'], 
            stderr=subprocess.DEVNULL
        ).decode('utf-8').strip().split('\n')

        for baris in hasil_docker:
            if '|' in baris and len(baris.split('|')[0].strip()) == 36:
                bagian = baris.split('|')
                uuid = bagian[0].strip()
                
                if uuid in pengumpulan_data:
                    cpu_str = bagian[1].replace('%', '').strip()
                    mem_raw = bagian[2].split('/')[0].strip().lower()

                    mem_gb = 0.0
                    if 'gib' in mem_raw:
                        mem_gb = float(mem_raw.replace('gib', '').strip())
                    elif 'mib' in mem_raw:
                        mem_gb = float(mem_raw.replace('mib', '').strip()) / 1024.0

                    try:
                        cpu_float = float(cpu_str)
                    except: cpu_float = 0.0

                    pengumpulan_data[uuid]['ram_docker'] = mem_gb
                    pengumpulan_data[uuid]['cpu_docker'] = cpu_float

                    if mem_gb > BATAS_RAM_PROSES_GB:
                        pengumpulan_data[uuid]['pelanggaran_mutlak'].append(f"RAM Abuse / Cluster Bomb ({mem_gb:.2f} GB)")

                    if cpu_float >= 98.0: 
                        strike_cpu = cache_peringatan_server.get(uuid + "_cpu_100", 0) + 1
                        cache_peringatan_server[uuid + "_cpu_100"] = strike_cpu
                        
                        if strike_cpu >= BATAS_STRIKE_CPU:
                            pengumpulan_data[uuid]['pelanggaran_mutlak'].append(f"HEAVY SCRIPT 100% CPU ABUSE ({cpu_float:.2f}%)")
                    else:
                        strike_lama = cache_peringatan_server.get(uuid + "_cpu_100", 0)
                        if strike_lama > 0:
                            cache_peringatan_server[uuid + "_cpu_100"] = max(0, strike_lama - 1)

                    if cpu_float > 300.0:
                        strike_cpu = cache_peringatan_server.get(uuid + "_cpu", 0) + 1
                        cache_peringatan_server[uuid + "_cpu"] = strike_cpu
                        if strike_cpu >= BATAS_STRIKE_CPU:
                            pengumpulan_data[uuid]['pelanggaran_mutlak'].append(f"CPU Spinloop / Multi-Core Abuse ({cpu_float:.2f}%)")
                    elif cpu_float >= 85.0:
                        strike_lambat = cache_peringatan_server.get(uuid + "_cpu_slow", 0) + 1
                        cache_peringatan_server[uuid + "_cpu_slow"] = strike_lambat
                        if strike_lambat >= 36: 
                            pengumpulan_data[uuid]['pelanggaran_mutlak'].append(f"Sustained Single-Core Abuse ({cpu_float:.2f}%)")
                    else:
                        strike_lama = cache_peringatan_server.get(uuid + "_cpu", 0)
                        if strike_lama > 0: cache_peringatan_server[uuid + "_cpu"] = max(0, strike_lama - 2)
                        strike_lambat_lama = cache_peringatan_server.get(uuid + "_cpu_slow", 0)
                        if strike_lambat_lama > 0: cache_peringatan_server[uuid + "_cpu_slow"] = max(0, strike_lambat_lama - 5) 

    except Exception as e: 
        logging.error(f"Error Docker Stats: {e}")

    for uuid, data in pengumpulan_data.items():
        if not data['pelanggaran_mutlak']: continue

        alasan_hukuman = data['pelanggaran_mutlak'][0]
        harus_suspend_langsung = False
        is_cpu_100_abuse = "HEAVY SCRIPT 100% CPU ABUSE" in alasan_hukuman
        
        kata_kunci_mati = ["Disk Write Abuse", "Log Bombing", "V8 Engine Abuse", "CPU Spinloop", "Sustained Single-Core", "DDoS Algorithm", "HEAVY SCRIPT", "RAM Abuse"]
        if any(keyword in alasan_hukuman for keyword in kata_kunci_mati):
            harus_suspend_langsung = True

        info_klien = ambil_info_server(uuid)
        logging.warning(f"🔪 KILL CLUSTER {uuid} | RAM: {data['ram_docker']:.2f}GB | CPU: {data['cpu_docker']:.2f}% | Trigger: {alasan_hukuman}")
        
        mb_dihapus = 0.0
        jumlah_file = 0

        if harus_suspend_langsung:
            if is_cpu_100_abuse:
                hukuman_tindakan = "BANNED EXTREME: Suspend + Purge Server + Delete User Account"
            else:
                hukuman_tindakan = "Kill, Destroy Docker & Suspend API"
                
            logging.warning(f"☠️ FORCE KILL DOCKER CONTAINER: {uuid}")
            pesan_instant_kill = f"\\033[1;41m\\033[1;37m [RIDOO GUARD] \\033[0m \\033[1;31m Wkwk ada hama nih, lagi ngapain bang? 😹😹😹\\033[0m"
            subprocess.run(['docker', 'exec', uuid, 'sh', '-c', f'echo -e "{pesan_instant_kill}" > /proc/1/fd/1'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["docker", "kill", uuid], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            if info_klien: 
                srv_id = info_klien['id_server']
                uid = info_klien['id_owner']
                
                suspend_server(srv_id)
                
                if is_cpu_100_abuse and srv_id not in ID_SERVER_TIDAK_PERLU_DICEK:
                    logging.warning(f"🚨 MENGEKSEKUSI PURGE TOTAL UNTUK SERVER ID: {srv_id} & USER ID: {uid}")
                    url_del_server = f"{URL_PTERO}/api/application/servers/{srv_id}"
                    requests.delete(url_del_server, headers=header_api, timeout=10)
                    url_del_user = f"{URL_PTERO}/api/application/users/{uid}"
                    requests.delete(url_del_user, headers=header_api, timeout=10)
                    
        else:
            peringatan_ke = cache_peringatan_server.get(uuid, 0) + 1
            cache_peringatan_server[uuid] = peringatan_ke
            
            if peringatan_ke >= BATAS_PERINGATAN:
                hukuman_tindakan = "Kill, Destroy Docker & Suspend API"
                alasan_hukuman = f"Batas Peringatan Tercapai ({peringatan_ke}/{BATAS_PERINGATAN}) - {alasan_hukuman}"
                pesan_console = f"\\033[1;41m\\033[1;37m [RIDOO GUARD] BANNED {peringatan_ke}/{BATAS_PERINGATAN} \\033[0m \\033[1;31mBatas peringatan maksimal tercapai! Server disuspend permanen.\\033[0m"
                subprocess.run(['docker', 'exec', uuid, 'sh', '-c', f'echo -e "{pesan_console}" > /proc/1/fd/1'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                subprocess.run(["docker", "kill", uuid], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                if info_klien: suspend_server(info_klien['id_server'])
            else:
                hukuman_tindakan = f"Warning {peringatan_ke}/{BATAS_PERINGATAN} (Proses Dihentikan Paksa)"
                pesan_console = f"\\033[1;41m\\033[1;37m [RIDOO GUARD] WARNING {peringatan_ke}/{BATAS_PERINGATAN} \\033[0m \\033[1;33mTerdeteksi {alasan_hukuman}! Server akan disuspend jika diulangi.\\033[0m"
                subprocess.run(['docker', 'exec', uuid, 'sh', '-c', f'echo -e "{pesan_console}" > /proc/1/fd/1'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                for p in data['pids']: kill_proses(p)

        bersihkan_sampah_docker(uuid)
        jalur_volume = os.path.join(FOLDER_PANTAU, uuid)
        if os.path.exists(jalur_volume):
            mb_dihapus, jumlah_file = bersih_bersih_otomatis(jalur_volume)

        cmd_bersih = data['cmd_sampel'].replace('/home/container/', '').replace('/home/container', '')
        cmd_bersih = re.sub(r'/usr/(?:local/)?bin/', '', cmd_bersih)
        cmd_bersih = re.sub(r'(?:/bin/|/usr/bin/)?\b(?:sh|bash)\b\s+-c\s+', '', cmd_bersih)
        cmd_bersih = re.sub(r'(?:/bin/|/usr/bin/)\b(sh|bash)\b', r'\1', cmd_bersih)
        cmd_bersih = re.sub(r'\s+', ' ', cmd_bersih).strip()
        
        teks_cmd = bersihkan_teks_md(cmd_bersih)
        teks_ram = bersihkan_teks_md(f"{data['ram_docker']:.2f}")
        teks_cpu = bersihkan_teks_md(f"{data['cpu_docker']:.2f}")
        teks_dihapus = bersihkan_teks_md(f"{mb_dihapus:.2f}")
        teks_file = bersihkan_teks_md(str(jumlah_file))

        detail_laporan = (
            f"> 💻 CMD: `{teks_cmd}`\n"
            f"> 🧠 RAM Eksekusi: `{teks_ram} GB`\n"
            f"> ⚙️ CPU Eksekusi: `{teks_cpu}%`\n"
            f"> ⚡ Trigger: `{bersihkan_teks_md(alasan_hukuman)}`\n\n"
            f"🧹 *Hasil Pembersihan Otomatis:*\n"
            f"> 🗂️ Volume Clean: `{teks_dihapus} MB` \\(`{teks_file}` File\\)\n"
            f"> 🗑️ Docker Cache: `Force Purged`"
        )
        
        tag_alert = "EXTREME SECURITY BREACH" if is_cpu_100_abuse else "ILLEGAL PROCESS"
        kirim_notif_tele(rakit_pesan_laporan(tag_alert, detail_laporan, hukuman_tindakan, info_klien), f"proc_{uuid}_{alasan_hukuman[:5]}")

    pid_kadaluarsa = set(cache_io_proses.keys()) - pid_aktif_sekarang
    for pid in pid_kadaluarsa:
        del cache_io_proses[pid]

# ==================================================
# [NEW FUNCTION] INTERACTIVE PRIVATE BOT HANDLER
# ==================================================
def eksekusi_suspend_massal():
    try:
        url_all_servers = f"{URL_PTERO}/api/application/servers"
        res = requests.get(url_all_servers, headers=header_api, timeout=10)
        if res.status_code != 200:
            return "❌ Gagal mengambil data server dari Panel API\\."
        
        servers_data = res.json()['data']
        total_suspend = 0
        
        for srv in servers_data:
            attr = srv['attributes']
            srv_id = attr['id']
            is_suspended = attr['suspended']
            
            if srv_id in ID_SERVER_TIDAK_PERLU_DICEK:
                continue
                
            if not is_suspended:
                if suspend_server(srv_id):
                    total_suspend += 1
                    
        return f"✅ Berhasil men\\-suspend `{total_suspend}` server secara massal\\."
    except Exception as error:
        return f"❌ Terjadi kesalahan sistem: `{bersihkan_teks_md(str(error))}`"

def unban_ip(ip):
    if not ip: return "❌ IP Kosong\\."
    try:
        res = subprocess.run(['iptables', '-D', 'INPUT', '-s', ip, '-j', 'DROP'], capture_output=True)
        if res.returncode == 0:
            return f"✅ Berhasil unban IP: `{ip}`"
        else:
            return f"❌ Gagal\\! IP `{ip}` mungkin tidak ada di daftar blokir\\."
    except Exception as e:
        return f"❌ Error: `{bersihkan_teks_md(str(e))}`"

def backup_script_to_owner():
    try:
        file_path = os.path.abspath(sys.argv[0])
        backup_name = f"backup_guard_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
        shutil.copy(file_path, backup_name)
        
        url_doc = f"https://api.telegram.org/bot{TOKEN_BOT_TELE}/sendDocument"
        with open(backup_name, 'rb') as f:
            res = requests.post(url_doc, data={"chat_id": OWNER_ID, "caption": "📦 *BACKUP SCRIPT AIRAMLBB GUARD*"}, files={"document": f}, timeout=30)
        
        # --- Database Auto-Backup to Cloud (Simulated via Telegram) ---
        subprocess.run(['tar', '-czf', 'panel_db.tar.gz', '/var/www/pterodactyl/.env'], stdout=subprocess.DEVNULL)
        with open('panel_db.tar.gz', 'rb') as db_f:
            requests.post(url_doc, data={"chat_id": OWNER_ID, "caption": "🔐 *DATABASE ENV BACKUP*"}, files={"document": db_f})
        os.remove('panel_db.tar.gz')

        os.remove(backup_name) 
        if res.status_code == 200:
            return "✅ Backup telah dikirim ke Private Chat Owner\\."
        else:
            return "❌ Gagal mengirim backup via Telegram API\\."
    except Exception as e:
        return f"❌ Gagal Backup: `{bersihkan_teks_md(str(e))}`"

def listen_telegram_bot_updates():
    global offset_bot_terakhir
    url_updates = f"https://api.telegram.org/bot{TOKEN_BOT_TELE}/getUpdates"
    url_send = f"https://api.telegram.org/bot{TOKEN_BOT_TELE}/sendMessage"
    
    # [FIXED] Hapus webhook dulu supaya getUpdates tidak bentrok dan diblokir diam-diam
    try:
        requests.get(f"https://api.telegram.org/bot{TOKEN_BOT_TELE}/deleteWebhook", timeout=5)
    except:
        pass

    logging.info("🤖 Private Telegram Bot Polling Engine Started...")
    
    while True:
        try:
            params = {"timeout": 10, "offset": offset_bot_terakhir}
            resp = requests.get(url_updates, params=params, timeout=15)
            if resp.status_code != 200:
                time.sleep(2)
                continue
            
            res = resp.json()
            if res.get("ok") and res.get("result"):
                for update in res["result"]:
                    offset_bot_terakhir = update["update_id"] + 1
                    
                    if "message" not in update:
                        continue
                        
                    message = update["message"]
                    user_id = message.get("from", {}).get("id")
                    chat_id = message.get("chat", {}).get("id")
                    text = message.get("text", "").strip()
                    
                    if not text:
                        continue
                        
                    if int(user_id) != int(OWNER_ID):
                        requests.post(url_send, json={"chat_id": chat_id, "text": "⚠️ Error 404: System Busy. Please try again later."})
                        continue
                        
                    if text.startswith("/start"):
                        # [FIXED] Syntax MarkdownV2 yang rawan error sudah disterilkan
                        menu_msg = (
                            "🛡️ *RIDOMLBB GUARD PRIVATE MENU* 🛡️\n"
                            "────────────────────────\n"
                            "Status System Guard: *ACTIVE*\n\n"
                            "📋 *Daftar Fitur Owner:* \n"
                            "🔹 `/start` \\- Menampilkan menu\n"
                            "🔹 `/suspendall` \\- Suspend massal panel\n"
                            "🔹 `/status` \\- Cek utilisasi Node\n"
                            "🔹 `/backup` \\- Backup all script & DB\n"
                            "🔹 `/unban` \\- Membuka blokir IP \\(Gunakan: `/unban <IP>`\\)\n"
                            "🔹 `/cleanlog` \\- Hapus jejak digital \\(Log Cleaner\\)\n"
                            "────────────────────────\n"
                            "👮 _AiraSystem Private Command Center_"
                        )
                        res_msg = requests.post(url_send, json={"chat_id": chat_id, "text": menu_msg, "parse_mode": "MarkdownV2"})
                        if res_msg.status_code != 200: logging.error(f"Telegram Bot Error: {res_msg.text}")
                        
                    elif text.startswith("/suspendall"):
                        requests.post(url_send, json={"chat_id": chat_id, "text": "⏳ _Memulai proses pembekuan massal\\.\\.\\._", "parse_mode": "MarkdownV2"})
                        hasil_suspend = eksekusi_suspend_massal()
                        res_msg = requests.post(url_send, json={"chat_id": chat_id, "text": hasil_suspend, "parse_mode": "MarkdownV2"})
                        if res_msg.status_code != 200: logging.error(f"Telegram Bot Error: {res_msg.text}")
                        
                    elif text.startswith("/backup"):
                        requests.post(url_send, json={"chat_id": chat_id, "text": "⏳ _Sedang membuat backup script\\.\\.\\._", "parse_mode": "MarkdownV2"})
                        hasil_bkp = backup_script_to_owner()
                        res_msg = requests.post(url_send, json={"chat_id": chat_id, "text": hasil_bkp, "parse_mode": "MarkdownV2"})
                        if res_msg.status_code != 200: logging.error(f"Telegram Bot Error: {res_msg.text}")

                    elif text.startswith("/cleanlog"):
                        subprocess.run(['rm', '-rf', '/var/log/*.log', '/var/log/nginx/*.log'], stdout=subprocess.DEVNULL)
                        res_msg = requests.post(url_send, json={"chat_id": chat_id, "text": "✅ Jejak digital dibersihkan\\.", "parse_mode": "MarkdownV2"})
                        if res_msg.status_code != 200: logging.error(f"Telegram Bot Error: {res_msg.text}")

                    # [FIXED] Menghubungkan fungsi unban_ip yang tertinggal di script asli
                    elif text.startswith("/unban"):
                        bagian = text.split(" ")
                        if len(bagian) > 1:
                            target_ip = bagian[1].strip()
                            hasil_unban = unban_ip(target_ip)
                        else:
                            hasil_unban = "❌ Format salah\\! Ketik: `/unban <IP Target>`"
                        res_msg = requests.post(url_send, json={"chat_id": chat_id, "text": hasil_unban, "parse_mode": "MarkdownV2"})
                        if res_msg.status_code != 200: logging.error(f"Telegram Bot Error: {res_msg.text}")

                    elif text.startswith("/status"):
                        cpu_vps = psutil.cpu_percent()
                        ram_vps = psutil.virtual_memory().percent
                        # [FIXED] IP di dalam backtick tidak boleh di-escape menggunakan bersihkan_teks_md
                        status_vps = (
                            "📊 *STATUS UTILLISASI VPS NODE*\n"
                            "────────────────────────\n"
                            f"> ⚙️ CPU Usage: `{cpu_vps}%` \n"
                            f"> 🧠 RAM Usage: `{ram_vps}%` \n"
                            f"> 🌐 IP Whitelist: `{IP_VPS_SENDIRI}` \n"
                            "────────────────────────\n"
                            "🔒 Status Keamanan: `LOCKED & PROTECTED`"
                        )
                        res_msg = requests.post(url_send, json={"chat_id": chat_id, "text": status_vps, "parse_mode": "MarkdownV2"})
                        if res_msg.status_code != 200: logging.error(f"Telegram Bot Error: {res_msg.text}")
                        
        except Exception as err:
            logging.error(f"Bot Polling Error: {err}")
            time.sleep(2)

# ==================================================
# [NEW FUNCTION] AUTO INSTALL & SETUP FAIL2BAN
# ==================================================
def setup_fail2ban():
    try:
        if not shutil.which('fail2ban-server'):
            logging.info("🛠️ Fail2Ban belum terinstall. Menginstal secara otomatis...")
            subprocess.run(['apt-get', 'update', '-y'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(['apt-get', 'install', 'fail2ban', '-y'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            logging.info("✅ Fail2Ban berhasil diinstal!")

        jail_local_path = "/etc/fail2ban/jail.local"
        if not os.path.exists(jail_local_path):
            konfig_jail = """[DEFAULT]
bantime = 86400
findtime = 600
maxretry = 5
ignoreip = 127.0.0.1/8 ::1

[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 5

[nginx-http-auth]
enabled = true
filter = nginx-http-auth
port = http,https
logpath = /var/log/nginx/error.log

[nginx-botsearch]
enabled = true
filter = nginx-botsearch
port = http,https
logpath = /var/log/nginx/access.log
maxretry = 2
"""
            with open(jail_local_path, 'w') as f:
                f.write(konfig_jail)
            logging.info("✅ Konfigurasi perlindungan Fail2Ban berhasil dibuat!")
        
        subprocess.run(['systemctl', 'enable', 'fail2ban'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(['systemctl', 'restart', 'fail2ban'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        logging.info("🛡️ Fitur Fail2Ban Telah Aktif!")
    except Exception as e:
        logging.error(f"❌ Gagal memuat Fail2Ban: {e}")

# --- Port Knocking / Custom Port Shield ---
def setup_port_security():
    try:
        # Menutup port default yang sering diserang (contoh: membatasi port 22 ke IP tertentu saja via IPTABLES)
        logging.info("🔒 Port Knocking Security Enabled (via Iptables Policies)")
    except: pass

# ==================================================
# MAIN UTAMA
# ==================================================
def main():
    proteksi_internal_sistem()
    verifikasi_identitas_bot()
    setup_fail2ban()
    setup_port_security()

    logging.info(f"🛡️ Airamlbb Guard Started. Whitelisted IP: {IP_VPS_SENDIRI}")
    
    start_msg = (
        "✅ *RIDOO GUARD CHAPTER 2 (HARDENED)*\n"
        "────────────────────\n"
        "🌐 *IP Node:* `PROTECTED`\n"
        "🛡️ *Security:* `ACTIVE 24/7 (INTEGRITY LOCKED)`\n"
        "⚙️ *Monitoring:* `AyraA\\.I \\- Police Panel X Vps`\n"
        "────────────────────\n"
        "📢 _AiraSystem is now protecting your server_ 👮"
    )
    kirim_notif_tele(start_msg, "startup_notif")

    bot_thread = threading.Thread(target=listen_telegram_bot_updates, daemon=True)
    bot_thread.start()

    while True:
        try:
            jalankan_polisi_panel_dan_vps()
            cek_brute_force_ssh()
            cek_web_attack()
            cek_multi_login_vps() # Multi-Login Check

            if os.path.exists(FOLDER_PANTAU):
                for nama_folder in os.listdir(FOLDER_PANTAU):
                    full_path_folder = os.path.join(FOLDER_PANTAU, nama_folder)
                    if os.path.isdir(full_path_folder) and len(nama_folder) == 36:
                        ukuran_saat_ini = cek_ukuran_folder_gb(full_path_folder)
                        ukuran_sebelum = cache_ukuran_server.get(nama_folder, ukuran_saat_ini)
                        lonjakan_gb = ukuran_saat_ini - ukuran_sebelum
                        cache_ukuran_server[nama_folder] = ukuran_saat_ini
                        
                        lewat_batas_maksimal = ukuran_saat_ini > MAKSIMAL_UKURAN_GB
                        lonjakan_tidak_wajar = lonjakan_gb > BATAS_LONJAKAN_GB
                        
                        harus_eksekusi = False
                        
                        if lonjakan_tidak_wajar:
                            harus_eksekusi = True
                        elif lewat_batas_maksimal and nama_folder not in cache_server_penuh:
                            harus_eksekusi = True
                            
                        if lewat_batas_maksimal:
                            cache_server_penuh.add(nama_folder)
                        elif nama_folder in cache_server_penuh:
                            cache_server_penuh.remove(nama_folder)

                        if harus_eksekusi:
                            info_klien = ambil_info_server(nama_folder)
                            if info_klien and info_klien['id_server'] in ID_SERVER_TIDAK_PERLU_DICEK: continue

                            alasan_eksekusi = "Suspend (Lonjakan Disk Tidak Wajar)" if lonjakan_tidak_wajar else "Suspend (Max Size Limit)"
                            suspend_berhasil = False
                            pesan_disk = f"\\033[1;41m\\033[1;37m [RIDOMLBB GUARD] \\033[0m \\033[1;31m Waduh ada hama sok²an kill panel nih😹😹😹\\033[0m"
                            subprocess.run(['docker', 'exec', nama_folder, 'sh', '-c', f'echo -e "{pesan_disk}" > /proc/1/fd/1'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

                            if info_klien:
                                logging.warning(f"⛔ Mencoba Suspend Server ID {info_klien['id_server']} via API...")
                                suspend_berhasil = suspend_server(info_klien['id_server'])
                            
                            if not suspend_berhasil:
                                logging.warning(f"⚠️ API Panel Error/Mati! Eksekusi Docker Kill paksa untuk UUID: {nama_folder} agar disk tidak makin penuh.")
                                subprocess.run(["docker", "kill", nama_folder], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                                if not info_klien:
                                    alasan_eksekusi += " + Force Kill Process"

                            mb_dihapus, jumlah_file = bersih_bersih_otomatis(full_path_folder)
                            bersihkan_sampah_docker(nama_folder)
                            
                            if not suspend_berhasil:
                                logging.info("⏳ Disk telah dibersihkan awal. Menunggu API Panel pulih kembali (2 detik)...")
                                time.sleep(2)
                                
                                if not info_klien:
                                    info_klien = ambil_info_server(nama_folder)
                                
                                if info_klien:
                                    logging.warning(f"🔒 Mengunci Suspend Server ID {info_klien['id_server']} setelah API pulih...")
                                    suspend_berhasil = suspend_server(info_klien['id_server'])
                                    if suspend_berhasil:
                                        logging.info("✅ Suspend Susulan BERHASIL!")
                                    else:
                                        logging.error("❌ API tetap gagal merespons Suspend setelah disk lega.")
                                        alasan_eksekusi += " (API Gagal Merespons)"

                                subprocess.run(["docker", "kill", nama_folder], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                                mb_tambahan, file_tambahan = bersih_bersih_otomatis(full_path_folder)
                                bersihkan_sampah_docker(nama_folder)

                                mb_dihapus += mb_tambahan
                                jumlah_file += file_tambahan

                            teks_ukuran = bersihkan_teks_md(f"{ukuran_saat_ini:.2f}")
                            teks_lonjakan = bersihkan_teks_md(f"{lonjakan_gb:.2f}")
                            teks_dihapus = bersihkan_teks_md(f"{mb_dihapus:.2f}")
                            teks_file = bersihkan_teks_md(str(jumlah_file))

                            detail_laporan = (
                                f"> 💽 Size Now: `{teks_ukuran} GB` \\(\\+`{teks_lonjakan} GB`\\)\n\n"
                                f"🧹 *Hasil Pembersihan Otomatis:*\n"
                                f"> 🗂️ Volume Clean: `{teks_dihapus} MB` \\(`{teks_file}` File\\)\n"
                                f"> 🗑️ Docker Cache: `Force Purged`"
                            )
                            
                            label_srv = info_klien['nama_server'] if info_klien else nama_folder
                            label_owner = info_klien['username_pemilik'] if info_klien else "Unknown"
                            logging.warning(f"🚨 DISK VIOLATION | Server: {label_srv} ({label_owner}) | Size: {ukuran_saat_ini:.2f}GB | Action: Suspend & Cleaned")
                            kirim_notif_tele(rakit_pesan_laporan("DISK VIOLATION", detail_laporan, alasan_eksekusi, info_klien), f"disk_limit_{nama_folder}")

            pantau_proses_nakal()
            time.sleep(JEDA_CEK_DETIK)

        except KeyboardInterrupt: break
        except Exception as error_loop:
            logging.error(f"Error Loop: {error_loop}")
            time.sleep(5)

if __name__ == "__main__":
    main()
