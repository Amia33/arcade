# Arcade

Useful scripts for arcade (osu! and maimai dx)

## osu! specific setting

You will need to apply for an `Oauth` token to use this script.  
Also, with no API endpoint for most-played maps, you have to load maps list manually and save it as `html` file.  
Be noted that this script doesn't handle duplicated items since I don't play osu anymore and this script is for archive usage.

To fill in values for `.env` file, use this url:  
`https://osu.ppy.sh/oauth/authorize?client_id=12345&redirect_uri=http://localhost:12345&response_type=code&scope=identify+public&state=check`  
Remember to replace values accordingly.
