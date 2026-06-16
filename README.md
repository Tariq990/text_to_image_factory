# Browser MCP With Personal Brave Profile

This folder documents the working setup that allowed opencode to control the existing personal Brave browser profile instead of opening a separate automated Brave window.

## Goal

Use the already-open personal Brave profile through the Browser MCP extension, so browser actions happen in the real user session, tabs, cookies, logins, and local network pages.

The confirmed working page after the fix was:

```text
http://192.168.1.1/#/home
```

Browser MCP successfully saw the personal Brave tab titled `Orange` for the `Flybox 4G+CP06` router page.

## What Was Going Wrong

The browser tool was not connected to the personal Brave profile. It kept opening a separate Brave window with empty tabs and the Browser MCP welcome page.

The separate window was caused by a Playwright MCP process that launched Brave with a temporary profile directory:

```text
C:\Users\tarik\AppData\Local\ms-playwright-mcp\mcp-chrome-for-testing-8bca82c
```

That temporary profile is not the personal Brave profile. It does not contain the user's normal tabs, cookies, logins, or extension state.

The process that revealed this was:

```text
@playwright/mcp@latest --browser=chromium --executable-path=C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe
```

Because of that process, the MCP browser tools were controlling the Playwright-created Brave profile, not the Brave profile where the Browser MCP extension had been connected.

## Important Difference

There are two different browser MCP approaches involved here:

```text
@playwright/mcp
```

This launches and controls its own browser context. If no `--user-data-dir` is provided, it creates a temporary profile under `ms-playwright-mcp`. This is why a new Brave window appeared.

```text
@browsermcp/mcp
```

This waits for the Browser MCP browser extension to connect from the real browser tab. This is the approach that works with the personal Brave profile.

## Fix That Made It Work

The global opencode config had the `opencode-browser` plugin enabled. That plugin caused the active browser tools to use Playwright MCP and open a temporary Brave profile.

The plugin was removed from:

```text
C:\Users\tarik\.config\opencode\opencode.json
```

Before the fix, the config ended with:

```json
{
  "plugin": [
    "opencode-browser"
  ]
}
```

After the fix, the plugin block was removed. The global config now keeps `browsermcp` enabled and leaves `playwright` disabled:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "playwright": {
      "command": "npx",
      "args": [
        "@playwright/mcp@latest",
        "--browser=chromium",
        "--executable-path=C:\\Program Files\\BraveSoftware\\Brave-Browser\\Application\\brave.exe"
      ],
      "enabled": false
    },
    "browsermcp": {
      "command": "npx",
      "args": [
        "@browsermcp/mcp@latest"
      ],
      "enabled": true,
      "type": "local"
    }
  }
}
```

The project config in this folder also enables Browser MCP:

```text
C:\Users\tarik\Desktop\mcp\opencode.json
```

```json
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "browsermcp": {
      "type": "local",
      "command": [
        "npx",
        "@browsermcp/mcp@latest"
      ],
      "enabled": true
    }
  }
}
```

## Required Restart

opencode reads config at startup. After removing `opencode-browser`, opencode had to be fully restarted.

Without a restart, the already-running Playwright MCP browser tools could still point at the temporary Brave profile.

## Correct Connection Steps

Use this order when reconnecting later:

1. Make sure opencode has been restarted after the config change.
2. Open the personal Brave profile normally.
3. Open the tab that should be controlled.
4. Click the Browser MCP extension icon in Brave.
5. Click `Connect` from that exact tab/window.
6. Ask opencode to inspect the browser.

When the connection is correct, Browser MCP should report the real tab URL from the personal Brave session, not `about:blank` or `https://docs.browsermcp.io/` from a new automated window.

## How We Confirmed It Worked

After restarting opencode and reconnecting from the personal Brave profile, Browser MCP returned this page:

```text
Page URL: http://192.168.1.1/#/home
Page Title: Orange
```

The snapshot included the router UI text:

```text
Flybox 4G+CP06
الاتصال متصل
شبكة 4G+
استخدامي
تسجيل الدخول كمسؤول
```

That confirmed the MCP tool was finally connected to the user's real Brave browser tab.

## Troubleshooting

If opencode says there is no browser extension connection, reconnect from the Brave extension:

```text
No connection to browser extension
```

If a new Brave window opens with empty tabs, the setup is probably using Playwright MCP again instead of Browser MCP extension mode.

Check for a temporary profile path like this in running Brave processes:

```text
ms-playwright-mcp
```

If it appears, make sure the `opencode-browser` plugin is not enabled and restart opencode.

## Key Takeaway

The working setup depends on using `@browsermcp/mcp` with the Browser MCP extension connected from the personal Brave profile, and not using `opencode-browser` or `@playwright/mcp` as the active browser controller.

## Quick Instructions For Any Agent

If another agent starts from zero, this is the shortest reliable path:

1. Do not use Playwright MCP browser tools for the personal Brave profile.
2. Use Browser MCP extension mode only.
3. Confirm `opencode-browser` is not enabled in `C:\Users\tarik\.config\opencode\opencode.json`.
4. Confirm `browsermcp` is enabled and points to `@browsermcp/mcp@latest`.
5. Restart opencode after any config change.
6. Tell the user to open the real Brave profile and click `Connect` from the Browser MCP extension in the target tab.
7. Use the Browser MCP snapshot tool and verify the returned URL matches the user's real tab.

Successful connection means the snapshot shows a real user tab, for example:

```text
Page URL: http://192.168.1.1/#/home
Page Title: Orange
```

Failed connection usually looks like one of these:

```text
No connection to browser extension
```

```text
Page URL: about:blank
Page Title: Welcome - Browser MCP
```

## Agent Do Not Do List

Do not re-enable this plugin:

```json
"plugin": [
  "opencode-browser"
]
```

Do not assume that launching Brave through Playwright means the personal profile is connected. This command opens an automation-controlled browser context and can create a temporary profile:

```text
npx @playwright/mcp@latest --browser=chromium --executable-path=C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe
```

Do not treat a Brave window as personal unless the process is using the normal Brave user data directory:

```text
C:\Users\tarik\AppData\Local\BraveSoftware\Brave-Browser\User Data
```

If the process uses this directory, it is not the personal profile:

```text
C:\Users\tarik\AppData\Local\ms-playwright-mcp\...
```

## Fast Process Check

On Windows, this command helps verify whether Playwright opened a temporary Brave profile:

```powershell
Get-CimInstance Win32_Process | Where-Object { $_.Name -match 'node|npx|brave' -and $_.CommandLine -match 'mcp|playwright|browsermcp|user-data-dir|remote-debugging' } | Format-List ProcessId,Name,CommandLine
```

Look for `ms-playwright-mcp`. If it appears in an active Brave process, that browser is not the personal Brave profile.

## Exact Working Mental Model

Browser MCP does not magically attach to every open browser. The connection is made by the Browser MCP extension from a specific Brave tab.

The correct flow is:

```text
opencode starts @browsermcp/mcp
personal Brave profile has Browser MCP extension installed
user clicks Connect in the extension from the target tab
Browser MCP tools now see that real tab
```

The incorrect flow is:

```text
opencode/plugin starts @playwright/mcp
Playwright launches Brave executable
Brave opens with a temporary ms-playwright-mcp profile
agent sees blank tabs instead of the user's real tabs
```

## Minimum Success Criteria

Before saying it works, an agent must verify all of these:

1. No active browser tool is controlling a Brave process under `ms-playwright-mcp`.
2. The Browser MCP extension reports connected in the user's personal Brave tab.
3. The snapshot returns the expected URL from the user's personal session.
4. The snapshot page content matches what the user sees on screen.

For this setup, the verified expected URL was:

```text
http://192.168.1.1/#/home
```
