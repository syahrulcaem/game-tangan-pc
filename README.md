# Rat Swat Game

Game Computer Vision interaktif berbasis Python, OpenCV, MediaPipe, dan Pygame. Pemain memakai tangan asli di depan webcam untuk menggerakkan cursor berbentuk paw dan memukul tikus sebelum waktu 60 detik habis.

## Fitur

- Hand tracking real-time dengan `MediaPipe Hands`
- Cursor paw dengan smoothing, anti-jitter, shadow, dan perubahan pose open/closed
- Tikus bergerak random, bounce di layar, dan punya animasi idle + hit
- Collision detection berbasis `rect.inflate()`
- UI score, timer, FPS, dan status webcam/hand
- Audio hit dan game over menggunakan `pygame.mixer`
- Struktur project modular dan OOP-friendly

## Struktur Project

```text
project/
|
|-- main.py
|-- settings.py
|-- game.py
|-- hand_tracking.py
|-- cursor.py
|-- rat.py
|-- effects.py
|-- sounds.py
|-- utils.py
|
|-- assets/
|
|-- requirements.txt
`-- README.md
```

## Asset yang Dipakai

Project ini memakai asset wajib berikut secara langsung:

- `D:\pengolahangame\rat.png`
- `D:\pengolahangame\bg.jpg`
- `D:\pengolahangame\paw1.png`
- `D:\pengolahangame\paw2.png`

## Instalasi

```bash
pip install -r requirements.txt
```

## Menjalankan Game

```bash
python main.py
```

## Cara Main

1. Pastikan webcam aktif.
2. Tampilkan satu tangan di depan kamera.
3. Gerakkan tangan untuk memindahkan paw.
4. Saat `landmark 12` lebih rendah dari `landmark 9`, sistem menganggap tangan tertutup.
5. Tutup tangan saat paw menyentuh tikus untuk mendapatkan score.
6. Setelah 60 detik, layar game over akan muncul dengan tombol restart dan exit.

## Catatan Teknis

- Jendela OpenCV preview menampilkan landmark tangan secara real-time.
- Tekan `q` pada jendela preview jika ingin menutup preview webcam tanpa menutup game.
- Tekan `Esc` di game untuk keluar.
- Suara dibuat secara procedural agar project tetap ringan dan tidak membutuhkan file audio tambahan.

## Penjelasan Singkat untuk Pemula

- `main.py` hanya bertugas menjalankan game.
- `game.py` adalah pusat alur permainan: update, draw, collision, UI, timer, dan game over.
- `hand_tracking.py` membaca webcam di thread terpisah agar game tetap smooth.
- `cursor.py` mengubah data tangan menjadi cursor paw yang halus.
- `rat.py` menyimpan perilaku tikus: spawn, gerak random, bounce, dan respawn.
- `effects.py` menampilkan efek visual saat tikus terkena.
- `sounds.py` membuat suara hit dan game over langsung dari kode.
- `settings.py` menyimpan semua angka penting supaya gampang diubah.

## Tips

- Jika gerakan cursor terasa terlalu cepat atau lambat, ubah nilai smoothing di `settings.py`.
- Jika webcam tidak terbaca, pastikan tidak sedang dipakai aplikasi lain.
