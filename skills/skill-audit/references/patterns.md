# Dangerous pattern catalog

Grep-able patterns for Section 4 of the SKILL.md. These are leads, not verdicts: every hit needs context before it becomes a finding.

## Network exfiltration

```
curl .* (-d|--data) 
wget .* --post-data
nc .* -e 
/dev/tcp/
requests\.post\(.*(password|token|secret|key)
fetch\(.*(password|token|secret|key)
```

## Download and execute

```
curl .* \| (ba)?sh
wget .* \| (ba)?sh
curl .* -o .* && chmod \+x
pip install .* --extra-index-url
npm install .*
```

## Decode and run (obfuscation)

```
base64 --?d.*\|.*(ba)?sh
base64\.b64decode.*exec
eval\(.*base64
powershell .*-e(ncodedCommand)?
```

## Credential access

```
~/.ssh/
~/.aws/
~/.gnupg/
~/.netrc
*_TOKEN|*_KEY|*_SECRET|*_PASSWORD
os\.environ(\.get)?\(.*(TOKEN|KEY|SECRET)
process\.env\..*(TOKEN|KEY|SECRET)
```

## Persistence

```
crontab
/etc/cron
LaunchAgents
systemd.*--user
>>.*\.bashrc|>>.*\.zshrc|>>.*profile
```

## Prompt-injection markers (inside SKILL.md)

```
ignore (all )?previous instructions
disregard (the|your|these) (rules|instructions|policies)
do not (mention|report|disclose)
mark (this|it) as safe
skip the audit
system prompt
```

## Notes

- A pattern hit in a comment or a test fixture is not the same as a hit in an install hook. Check where the match lives.
- Absence of hits is not proof of safety. It means the cheap static pass found nothing.
- New obfuscation shows up constantly. Treat this list as a starting set and extend it when you see something novel.
