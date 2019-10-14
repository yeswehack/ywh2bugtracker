from ywh2bt.ywh2bt import main

if __name__ == "__main__":

    defaults = {
        "ywh_url_api": "http://api.ywh.docker.local",
        "supported_bugtracker": ["gitlab", "jira", "github"],
    }
    main()
