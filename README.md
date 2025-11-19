# dudeatron

A buddy to help me manage my wireless network.

I hope you find something here useful. 

## Features

- [ ] Add support for SSHing to APs and then running & parsing the following commands:
  - [ ] `show version`
  - [ ] `show inventory`
- [ ] Add support for SSHing to WLCs and then running & parsing the following commands:
  - [ ] `show version`
  - [ ] `show inventory`
  - [ ] `show ap summary`
  - [ ] `show ap summary load-info`
  - [ ] `show ap uptime`
  - [ ] `show ap name $AP_NAME config general`
  - [ ] `show ap name $AP_NAME ethernet statistics`
  - [ ] `show ap cdp neighbors`
- [ ] Implement `python-dotenv` for configuration management
- [ ] Add data output to the following
  - [ ] Data output to json files
  - [ ] Data output to a time series database
  - [ ] Data output to Prometheus
  - [ ] Data output to CSV files with comprehensive data flattening
- [ ] Add example visualizations using Grafana
- [ ] Add support for multiple SSH connections at once
- [ ] Add support for pulling equiptment lists (e.g. APs, WLCs) from Cisco DNA Center
- [ ] Add support for pulling equiptment lists (e.g. APs, WLCs) from netbox
- [ ] Help with AP replacement projects
  - [ ] Keep track of AP to switchport relationships
  - [ ] As APs get replaced, generate code snippets to configure APs
    - [ ] Set AP name
    - [ ] Set Primary Controller
    - [ ] Add AP to location ( ap location name $BuildingCode-location )
    - [ ] Set AP height
  - [ ] Update project status in Asana
  - [ ] Generate config archives
    - [ ] `show ap name $AP_NAME config general`
    - [ ] `show ap name $AP_NAME ethernet statistics`
    - [ ] `show ap name $AP_NAME cdp neighbors`
    - [ ] `show ap meraki monitoring summary`
    - [ ] `show ap name $AP_NAME inventory`


## AI Disclosure

**Here there be robots!** I *think* they are friendly, but they might just be very good at pretending. You might be a fool if you use this project for anything other than as an example of how silly it can be to use AI to code with.

> This project was developed with the assistance of language models from companies such as OpenAI and Anthropic, which provided suggestions and code snippets to enhance the functionality and efficiency of the tools. The models were used to generate code, documentation, distraction, moral support, moral turpitude, and explanations for various components of the project.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
