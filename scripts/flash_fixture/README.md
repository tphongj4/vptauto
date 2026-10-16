# Local Flash input fixture

`Main.hx` draws the login/channel/three-character layouts and handles actual
Flash `MouseEvent.CLICK` events. Force keeps the original login buttons visible
behind an animated progress dialog for eight seconds before opening channels,
simulating the server disconnecting an existing session. Entering replaces the
scene with a solid color that encodes the selected slot; repeated Force clicks
produce a failure color. The native smoke test checks this color. It makes no
network requests and uses no game assets, accounts or URLs. Unit tests also
exercise waits up to 180 seconds using an injected clock.

Rebuild `login.swf` with Haxe 4.3.6:

```sh
haxe -cp scripts/flash_fixture -main Main -swf scripts/flash_fixture/login.swf -swf-version 11.4 -D swf-header=852:553:25:101010
```

On Windows, test with an existing projector:

```powershell
python scripts/smoke_flash_windows.py --player 'C:\Tools\flashplayer25sa.exe'
```

Without `--player`, the test downloads a checksum-pinned Flash Projector 32
into a temporary directory. It is not distributed with VPT Auto. This tests
native Flash input, not Vua Pháp Thuật's own controls or server login.

`scripts/probe_flash_windows.py --player <path> --output <folder>` compares
message delivery methods on this same local movie and saves test images. It
never opens saved game links or moves the physical pointer.
