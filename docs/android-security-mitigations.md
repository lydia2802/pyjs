# Android Security Mitigations — MITRE ATT&CK for Mobile

Dokumen ini merangkum **seluruh daftar Mitigations** pada framework **MITRE ATT&CK® for Mobile**
(matrix: Mobile), yang digunakan untuk mengamankan perangkat Android (dan iOS) dari teknik-teknik
serangan (Techniques/Tactics) yang terdaftar di matrix tersebut.

Referensi resmi: https://attack.mitre.org/mitigations/mobile/

> Catatan: Link OneDrive yang diberikan tidak dapat diakses oleh agent ini (HTTP 403 — butuh
> autentikasi/akses akun). Isi dokumen ini disusun berdasarkan basis pengetahuan terhadap framework
> publik MITRE ATT&CK for Mobile, yang formatnya cocok dengan contoh (`M1012 — Enterprise Policy`)
> yang diberikan di permintaan.

---

## Daftar Ringkas (Index)

| ID | Nama Mitigasi | Kategori |
|----|----------------|----------|
| [M1001](#m1001--security-updates) | Security Updates | Patch Management |
| [M1002](#m1002--attestation) | Attestation | Device Integrity |
| [M1003](#m1003--enterprise-application-store) | Enterprise Application Store | App Distribution |
| [M1004](#m1004--system-partition-integrity) | System Partition Integrity | Device Integrity |
| [M1005](#m1005--application-vetting) | Application Vetting | App Security |
| [M1006](#m1006--use-recent-os-version) | Use Recent OS Version | Patch Management |
| [M1007](#m1007--caution-with-device-administrator-access) | Caution with Device Administrator Access | Access Control |
| [M1008](#m1008--application-isolation) | Application Isolation | App Security |
| [M1009](#m1009--encrypt-network-traffic) | Encrypt Network Traffic | Network Security |
| [M1010](#m1010--deploy-compromised-device-detection-method) | Deploy Compromised Device Detection Method | Device Integrity |
| [M1011](#m1011--user-guidance) | User Guidance | Awareness |
| [M1012](#m1012--enterprise-policy) | Enterprise Policy | Access Control |
| [M1013](#m1013--application-developer-guidance) | Application Developer Guidance | App Security |

---

## M1001 — Security Updates

- **ID**: M1001
- **Nama**: Security Updates
- **Nama Produk/Komponen**: Android OTA Update Service, Google Play System Updates, OEM Firmware Update (Samsung, Pixel, Xiaomi, dll), EMM/MDM (Intune, Workspace ONE, Google Endpoint Management)
- **Fungsi/Kegunaan**: Memastikan perangkat selalu menjalankan patch keamanan terbaru sehingga celah (CVE) yang sudah diketahui publik tidak dapat dieksploitasi.
- **Deskripsi**: Mendorong/mewajibkan pembaruan sistem operasi dan firmware secara rutin. Banyak teknik serangan mobile (privilege escalation, exploit kernel) mengandalkan kerentanan yang sudah memiliki patch resmi namun belum diterapkan oleh pengguna/organisasi.
- **Contoh Mitigasi**:
  - Mewajibkan instalasi patch keamanan bulanan (Android Security Bulletin) maksimal 30 hari setelah rilis.
  - Menonaktifkan akses korporat (conditional access) bagi device dengan patch level di luar ambang yang ditentukan.
- **Contoh Kode/API**:
  ```kotlin
  // Memeriksa patch level keamanan device (untuk compliance check di MDM agent)
  val patchLevel = Build.VERSION.SECURITY_PATCH // contoh: "2024-05-01"
  ```
  ```java
  // EMM API - Android Management API: cek complianceState perangkat
  GET https://androidmanagement.googleapis.com/v1/enterprises/{enterpriseId}/devices/{deviceId}
  // response field: "securityPatchLevel", "appliedState"
  ```
- **GUI**: Google Admin Console → *Devices → Mobile & endpoints → Settings → Compliance → Minimum Android security patch level*.
- **Link**: https://attack.mitre.org/mitigations/M1001/

---

## M1002 — Attestation

- **ID**: M1002
- **Nama**: Attestation
- **Nama Produk/Komponen**: Google Play Integrity API (pengganti SafetyNet Attestation), Samsung Knox Attestation, Android Keystore Hardware Attestation
- **Fungsi/Kegunaan**: Memverifikasi integritas perangkat dan aplikasi (apakah bootloader unlocked, rooted, atau berjalan di emulator) sebelum mengizinkan akses ke data/layanan sensitif.
- **Deskripsi**: Attestation menggunakan hardware root-of-trust untuk membuktikan bahwa device berjalan pada firmware resmi, belum di-root, dan aplikasi tidak dimodifikasi (repackaged).
- **Contoh Mitigasi**: Aplikasi perbankan memanggil Play Integrity API sebelum menampilkan layar transaksi; jika `deviceIntegrity` gagal, transaksi diblokir.
- **Contoh Kode/API**:
  ```kotlin
  val integrityManager = IntegrityManagerFactory.create(applicationContext)
  val request = IntegrityTokenRequest.builder()
      .setNonce(nonce)
      .setCloudProjectNumber(CLOUD_PROJECT_NUMBER)
      .build()
  integrityManager.requestIntegrityToken(request)
      .addOnSuccessListener { response ->
          val token = response.token() // dikirim ke server untuk diverifikasi
      }
  ```
  ```bash
  # Server-side verification (Google Play Integrity API)
  POST https://playintegrity.googleapis.com/v1/{packageName}:decodeIntegrityToken
  ```
- **GUI**: Play Console → *App integrity → Play Integrity API → Enable*.
- **Link**: https://attack.mitre.org/mitigations/M1002/

---

## M1003 — Enterprise Application Store

- **ID**: M1003
- **Nama**: Enterprise Application Store
- **Nama Produk/Komponen**: Google Play Managed Apps, Microsoft Intune Company Portal, Samsung Knox Store, AppConfig
- **Fungsi/Kegunaan**: Mendistribusikan aplikasi yang sudah disetujui (whitelisted) ke perangkat korporat, mencegah instalasi aplikasi dari sumber tidak terverifikasi (sideload).
- **Deskripsi**: Organisasi mengontrol katalog aplikasi yang boleh dipasang melalui *managed Google Play* sehingga risiko dari aplikasi berbahaya (malware, trojan) dari luar (APK sideload, third-party store) dapat dikurangi.
- **Contoh Mitigasi**: EMM mendorong daftar aplikasi wajib (`force-install`) dan memblokir Play Store konsumer biasa pada profil kerja (Work Profile).
- **Contoh Kode/API**:
  ```json
  // Android Management API - applyPolicy: daftar aplikasi yang diizinkan
  {
    "applications": [
      { "packageName": "com.company.app", "installType": "FORCE_INSTALLED" }
    ],
    "playStoreMode": "WHITELIST"
  }
  ```
- **GUI**: Google Admin Console → *Apps → Web and mobile apps → Add app → Manage by organizational unit*.
- **Link**: https://attack.mitre.org/mitigations/M1003/

---

## M1004 — System Partition Integrity

- **ID**: M1004
- **Nama**: System Partition Integrity
- **Nama Produk/Komponen**: Android Verified Boot (AVB / dm-verity), SELinux Enforcing Mode
- **Fungsi/Kegunaan**: Melindungi partisi sistem (`/system`, `/vendor`, `/boot`) agar tidak dapat dimodifikasi tanpa terdeteksi, mencegah malware persisten di level firmware.
- **Deskripsi**: Verified Boot memverifikasi setiap tahap booting (bootloader → kernel → system) menggunakan tanda tangan kriptografis. Jika partisi dimodifikasi (root custom, malware sistem), perangkat akan menampilkan peringatan atau gagal booting.
- **Contoh Mitigasi**: Menolak akses korporat jika status verified boot = `orange`/`red` (modified/failed) berdasarkan SafetyNet/Play Integrity report.
- **Contoh Kode/API**:
  ```kotlin
  // Cek status verified boot via Play Integrity verdict
  // response.deviceIntegrity.deviceRecognitionVerdict
  // nilai: MEETS_DEVICE_INTEGRITY, MEETS_BASIC_INTEGRITY, dll.
  ```
- **GUI**: Tidak ada GUI langsung untuk end-user; dikonfigurasi oleh OEM saat build firmware (`BOARD_AVB_ENABLE := true` di `BoardConfig.mk`, AOSP).
- **Link**: https://attack.mitre.org/mitigations/M1004/

---

## M1005 — Application Vetting

- **ID**: M1005
- **Nama**: Application Vetting
- **Nama Produk/Komponen**: Google Play Protect, VirusTotal Mobile, MobSF (Mobile Security Framework), NowSecure
- **Fungsi/Kegunaan**: Menganalisis aplikasi (statis & dinamis) sebelum/selama didistribusikan untuk mendeteksi perilaku berbahaya (malware, spyware, izin berlebihan).
- **Deskripsi**: Proses vetting memeriksa kode APK, permission yang diminta, komunikasi jaringan, dan perilaku runtime aplikasi pihak ketiga sebelum disetujui masuk ke enterprise app store.
- **Contoh Mitigasi**: Kebijakan internal mewajibkan setiap APK BYOD discan via MobSF API sebelum disetujui MDM.
- **Contoh Kode/API**:
  ```bash
  # MobSF REST API - upload & scan APK
  curl -F "file=@app.apk" https://mobsf.local/api/v1/upload -H "Authorization: <API_KEY>"
  curl -X POST https://mobsf.local/api/v1/scan -d "hash=<FILE_HASH>" -H "Authorization: <API_KEY>"
  ```
- **GUI**: MobSF Web UI (`http://localhost:8000`) → upload APK → laporan otomatis (skor risiko, daftar permission, CVE).
- **Link**: https://attack.mitre.org/mitigations/M1005/

---

## M1006 — Use Recent OS Version

- **ID**: M1006
- **Nama**: Use Recent OS Version
- **Nama Produk/Komponen**: Android OS (versi terbaru), Google Endpoint Management, Samsung Knox
- **Fungsi/Kegunaan**: Memastikan device menjalankan versi Android dengan fitur keamanan terbaru (Scoped Storage, Runtime Permission granular, Privacy Sandbox).
- **Deskripsi**: Setiap rilis Android baru memperkenalkan mitigasi tambahan terhadap teknik serangan yang sudah dikenal (misal: pembatasan akses Accessibility Service, restricted settings untuk sideloaded apps di Android 13+).
- **Contoh Mitigasi**: Kebijakan compliance menolak device dengan API level < 31 (Android 12) untuk akses email korporat.
- **Contoh Kode/API**:
  ```json
  // Android Management API policy
  { "minimumApiLevel": 31 }
  ```
- **GUI**: Google Admin Console → *Compliance → Minimum Android version*.
- **Link**: https://attack.mitre.org/mitigations/M1006/

---

## M1007 — Caution with Device Administrator Access

- **ID**: M1007
- **Nama**: Caution with Device Administrator Access
- **Nama Produk/Komponen**: Android `DeviceAdminReceiver`, Android Enterprise (Work Profile/Fully Managed)
- **Fungsi/Kegunaan**: Membatasi/mengontrol aplikasi mana yang boleh meminta hak Device Administrator (legacy API) karena hak ini dapat disalahgunakan malware (mengunci device, mencegah uninstall).
- **Deskripsi**: API Device Administrator legacy memberi kontrol tingkat tinggi atas device (wipe, lock, password policy). Malware sering menyalahgunakan ini agar tidak bisa di-uninstall. Solusi modern: migrasi ke Android Enterprise (Work Profile) yang lebih granular dan diisolasi.
- **Contoh Mitigasi**: Memblokir instalasi aplikasi non-EMM yang meminta `BIND_DEVICE_ADMIN`; edukasi user untuk waspada saat prompt "Activate device admin app?" muncul.
- **Contoh Kode/API**:
  ```xml
  <!-- AndroidManifest.xml -->
  <receiver android:name=".MyDeviceAdminReceiver"
      android:permission="android.permission.BIND_DEVICE_ADMIN">
      <meta-data android:name="android.app.device_admin"
          android:resource="@xml/device_admin_policies" />
      <intent-filter>
          <action android:name="android.app.action.DEVICE_ADMIN_ENABLED" />
      </intent-filter>
  </receiver>
  ```
- **GUI**: Settings → *Security → Device admin apps* (Android) → tampilkan daftar app yang punya akses, user dapat mencabut.
- **Link**: https://attack.mitre.org/mitigations/M1007/

---

## M1008 — Application Isolation

- **ID**: M1008
- **Nama**: Application Isolation
- **Nama Produk/Komponen**: Android Sandbox (per-UID), SELinux, Work Profile (Android Enterprise)
- **Fungsi/Kegunaan**: Mengisolasi data dan eksekusi antar aplikasi sehingga aplikasi berbahaya tidak dapat mengakses data aplikasi lain secara langsung.
- **Deskripsi**: Setiap aplikasi Android berjalan dengan UID Linux unik dan sandbox proses sendiri. Work Profile menambah isolasi lapis kedua antara data pribadi dan data kerja dalam satu device fisik.
- **Contoh Mitigasi**: Mengaktifkan Work Profile sehingga data korporat (email, file) tidak dapat diakses oleh aplikasi pribadi pada profil yang berbeda.
- **Contoh Kode/API**:
  ```kotlin
  // Membuat managed profile (dipanggil oleh DPC - Device Policy Controller)
  val dpm = getSystemService(DevicePolicyManager::class.java)
  dpm.createAndManageUser(
      admin, "WorkProfile", profileOwnerComponent, null,
      DevicePolicyManager.MAKE_USER_EPHEMERAL
  )
  ```
- **GUI**: Settings → *Work profile settings* → toggle "Work apps" on/off (ikon koper/badge biru pada app icon).
- **Link**: https://attack.mitre.org/mitigations/M1008/

---

## M1009 — Encrypt Network Traffic

- **ID**: M1009
- **Nama**: Encrypt Network Traffic
- **Nama Produk/Komponen**: TLS/HTTPS, Android Network Security Config, VPN (Always-on VPN by EMM)
- **Fungsi/Kegunaan**: Mencegah penyadapan (sniffing) dan manipulasi (MITM) lalu lintas jaringan aplikasi melalui jaringan tidak tepercaya (misal Wi-Fi publik).
- **Deskripsi**: Mewajibkan seluruh komunikasi aplikasi menggunakan TLS dengan certificate pinning, serta menonaktifkan trafik HTTP cleartext.
- **Contoh Mitigasi**: Mengatur `usesCleartextTraffic="false"` dan menerapkan *Always-on VPN* via MDM agar semua trafik korporat melalui terowongan terenkripsi.
- **Contoh Kode/API**:
  ```xml
  <!-- res/xml/network_security_config.xml -->
  <network-security-config>
      <base-config cleartextTrafficPermitted="false">
          <trust-anchors>
              <certificates src="system" />
          </trust-anchors>
      </base-config>
      <domain-config>
          <domain includeSubdomains="true">api.company.com</domain>
          <pin-set expiration="2026-01-01">
              <pin digest="SHA-256">base64==pin1</pin>
          </pin-set>
      </domain-config>
  </network-security-config>
  ```
  ```json
  // Android Management API - Always-on VPN
  { "alwaysOnVpnPackage": { "packageName": "com.vpn.client", "lockdownEnabled": true } }
  ```
- **GUI**: Google Admin Console → *Networks → Always-on VPN*; atau Settings → *Network & internet → VPN*.
- **Link**: https://attack.mitre.org/mitigations/M1009/

---

## M1010 — Deploy Compromised Device Detection Method

- **ID**: M1010
- **Nama**: Deploy Compromised Device Detection Method
- **Nama Produk/Komponen**: Google Play Protect, Lookout Mobile Endpoint Security, Zimperium zIPS, MDM Compliance Engine
- **Fungsi/Kegunaan**: Mendeteksi indikasi device root/jailbreak, malware terinstal, atau konfigurasi berisiko secara berkelanjutan (bukan hanya saat enrolment).
- **Deskripsi**: Solusi MTD (Mobile Threat Defense) memantau device secara real-time untuk root detection, network anomaly, app risk scoring, lalu mengintegrasikan hasilnya dengan EMM agar device "compromised" otomatis diblokir/dikarantina.
- **Contoh Mitigasi**: Integrasi Lookout MTD ↔ Microsoft Intune Conditional Access — device dengan skor risiko "High" otomatis kehilangan akses Office 365.
- **Contoh Kode/API**:
  ```kotlin
  // Contoh deteksi root sederhana (client-side, indikatif - bukan jaminan)
  fun isDeviceRooted(): Boolean {
      val paths = arrayOf("/system/app/Superuser.apk", "/sbin/su", "/system/bin/su")
      return paths.any { File(it).exists() }
  }
  ```
- **GUI**: Microsoft Endpoint Manager → *Endpoint security → Conditional access → App protection based on device risk*.
- **Link**: https://attack.mitre.org/mitigations/M1010/

---

## M1011 — User Guidance

- **ID**: M1011
- **Nama**: User Guidance
- **Nama Produk/Komponen**: Security Awareness Training (KnowBe4, Proofpoint), Internal Security Policy/SOP
- **Fungsi/Kegunaan**: Mengedukasi pengguna agar tidak melakukan tindakan berisiko (instal APK dari sumber tidak resmi, memberi izin Accessibility ke aplikasi tidak dikenal, klik link phishing SMS/WhatsApp).
- **Deskripsi**: Banyak teknik serangan mobile (smishing, fake app, social engineering untuk minta izin Accessibility) bergantung pada interaksi pengguna. Edukasi rutin mengurangi tingkat keberhasilan serangan ini.
- **Contoh Mitigasi**: Kampanye internal rutin: "Jangan pernah aktifkan USB Debugging / Unknown Sources kecuali diminta tim IT", simulasi phishing SMS triwulanan.
- **Contoh Implementasi (non-kode)**: SOP onboarding karyawan baru wajib membaca & menandatangani kebijakan BYOD/penggunaan perangkat mobile.
- **GUI**: N/A (proses non-teknis); biasanya disampaikan via portal LMS (Learning Management System) korporat.
- **Link**: https://attack.mitre.org/mitigations/M1011/

---

## M1012 — Enterprise Policy

- **ID**: M1012
- **Nama**: Enterprise Policy
- **Nama Produk/Komponen**: Android `DevicePolicyManager` (EMM/MDM seperti Microsoft Intune, Google Endpoint Management, VMware Workspace ONE, Samsung Knox Manage)
- **Fungsi/Kegunaan**: Menerapkan kebijakan keamanan terpusat pada perangkat terdaftar (managed) agar fitur berisiko (ADB, Accessibility Service tidak terverifikasi, instalasi dari sumber tidak dikenal) dapat dibatasi/diblokir oleh organisasi.
- **Deskripsi (lengkap, sesuai contoh permintaan)**:
  Enterprise policies should block access to the **Android Debug Bridge (ADB)** by preventing users
  from enabling **USB debugging** on Android devices unless specifically needed (misal: device
  tersebut digunakan untuk application development). Sebuah EMM/MDM dapat menggunakan method
  `DevicePolicyManager.setPermittedAccessibilityServices` untuk mengatur daftar eksplisit aplikasi
  yang diizinkan menggunakan fitur Accessibility Android — sehingga malware yang menyalahgunakan
  Accessibility Service (overlay attack, auto-click, credential theft) untuk mendapatkan kontrol
  penuh atas UI device dapat dicegah.
- **Contoh Mitigasi**:
  1. Blokir USB Debugging/ADB pada device korporat kecuali untuk profil "Developer" tertentu.
  2. Whitelist aplikasi Accessibility Service yang diizinkan (misal hanya aplikasi screen-reader resmi/EMM agent).
  3. Blokir instalasi dari "Unknown Sources" (sideloading) di luar profil kerja.
  4. Wajibkan password/PIN kompleksitas tinggi via `setPasswordQuality`.
- **Contoh Kode/API**:
  ```kotlin
  // 1. Memblokir USB debugging / mencegah developer settings (di profil terkelola)
  val dpm = context.getSystemService(DevicePolicyManager::class.java)
  dpm.addUserRestriction(adminComponent, UserManager.DISALLOW_DEBUGGING_FEATURES)
  // mencegah user mengaktifkan toggle "USB debugging" pada Developer Options

  // 2. Membatasi Accessibility Service yang diizinkan (whitelist eksplisit)
  val allowedServices = listOf("com.company.emmagent/.AccessibilityHelperService")
  dpm.setPermittedAccessibilityServices(adminComponent, allowedServices)
  // null = semua diizinkan (default, TIDAK aman); list kosong [] = tidak ada yang diizinkan

  // 3. Memblokir instalasi aplikasi dari sumber tidak diketahui
  dpm.addUserRestriction(adminComponent, UserManager.DISALLOW_INSTALL_UNKNOWN_SOURCES)

  // 4. Mewajibkan kebijakan password kompleks
  dpm.setPasswordQuality(adminComponent, DevicePolicyManager.PASSWORD_QUALITY_COMPLEX)
  dpm.setPasswordMinimumLength(adminComponent, 8)
  ```
  ```json
  // Android Management API (versi cloud, tanpa kode native DPC) — policy.json
  {
    "debuggingFeaturesAllowed": false,
    "permittedAccessibilityServices": {
      "packageNames": ["com.company.emmagent"]
    },
    "installUnknownSourcesAllowed": false,
    "passwordPolicies": [
      { "passwordQuality": "COMPLEX", "passwordMinimumLength": 8 }
    ]
  }
  ```
  ```bash
  # Menerapkan policy ke device via Android Management API (REST)
  curl -X PATCH \
    "https://androidmanagement.googleapis.com/v1/enterprises/{enterpriseId}/policies/{policyId}" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d @policy.json
  ```
- **GUI**:
  - **Google Admin Console** → *Devices → Mobile & endpoints → Settings → Android settings*:
    - "USB debugging" → `Disallow` (kecuali OU developer khusus).
    - "Accessibility services" → tambahkan daftar package yang diizinkan secara eksplisit.
    - "Unknown sources" → `Disallow`.
  - **Microsoft Intune** → *Devices → Configuration profiles → Android Enterprise → Device restrictions* → bagian *General* (USB debugging) dan *App* (Accessibility services control).
  - **Samsung Knox Manage** → *Policy → Application → Accessibility Service Whitelist*.
- **Link**: https://attack.mitre.org/mitigations/M1012/

---

## M1013 — Application Developer Guidance

- **ID**: M1013
- **Nama**: Application Developer Guidance
- **Nama Produk/Komponen**: Android Secure Coding Guidelines, OWASP Mobile Application Security Verification Standard (MASVS), Google Play App Signing
- **Fungsi/Kegunaan**: Memberikan panduan praktik aman bagi developer aplikasi Android (penyimpanan data, kriptografi, validasi input) agar aplikasi tidak menjadi vektor serangan.
- **Deskripsi**: Mencakup praktik seperti penggunaan `EncryptedSharedPreferences`/Android Keystore untuk data sensitif, menghindari hardcoded secret, validasi deep link/intent untuk mencegah Intent Hijacking, serta mengikuti checklist OWASP MASVS sebelum rilis.
- **Contoh Mitigasi**: Code review wajib menggunakan checklist OWASP MASTG sebelum merge ke branch release; static analysis (`./gradlew lint`, MobSF) dijalankan di CI/CD.
- **Contoh Kode/API**:
  ```kotlin
  // Menyimpan data sensitif dengan EncryptedSharedPreferences (bukan SharedPreferences biasa)
  val masterKey = MasterKey.Builder(context)
      .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
      .build()
  val encryptedPrefs = EncryptedSharedPreferences.create(
      context, "secure_prefs", masterKey,
      EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
      EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
  )
  ```
  ```xml
  <!-- Validasi exported component agar tidak bisa dipanggil sembarang app -->
  <activity android:name=".SensitiveActivity" android:exported="false" />
  ```
- **GUI**: Android Studio → *Analyze → Run Inspection by Name → "Security"* (lint security checks bawaan IDE).
- **Link**: https://attack.mitre.org/mitigations/M1013/

---

## Ringkasan Pemetaan GUI & API per Kategori

| Kategori | Contoh GUI Admin | Contoh API/Kode |
|---|---|---|
| Patch & OS Version (M1001, M1006) | Google Admin Console → Compliance | Android Management API `securityPatchLevel`, `minimumApiLevel` |
| Device Integrity (M1002, M1004, M1010) | Play Console → App integrity | Play Integrity API `IntegrityManager`, `decodeIntegrityToken` |
| App Distribution & Vetting (M1003, M1005) | Google Admin Console → Apps | Android Management API `applications[]`, MobSF REST API |
| Access Control (M1007, M1008, M1012) | Settings → Device admin apps / Work profile / Knox Manage | `DevicePolicyManager` (`setPermittedAccessibilityServices`, `addUserRestriction`, `setPasswordQuality`) |
| Network Security (M1009) | Admin Console → Always-on VPN | `network_security_config.xml`, `alwaysOnVpnPackage` |
| Awareness & Dev Guidance (M1011, M1013) | LMS Portal / Android Studio Lint | OWASP MASVS checklist, `EncryptedSharedPreferences` |

---

## Referensi

- MITRE ATT&CK for Mobile — Mitigations: https://attack.mitre.org/mitigations/mobile/
- MITRE ATT&CK Mobile Matrix: https://attack.mitre.org/matrices/mobile/
- Android `DevicePolicyManager` API Reference: https://developer.android.com/reference/android/app/admin/DevicePolicyManager
- Android Management API: https://developers.google.com/android/management
- Google Play Integrity API: https://developer.android.com/google/play/integrity
- OWASP Mobile Application Security (MASVS/MASTG): https://owasp.org/www-project-mobile-app-security/
