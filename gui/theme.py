"""Dark and light palettes for the OnionGate desktop interface."""


DARK_THEME = """
QWidget { color: #E7EDF6; font-family: Arial; font-size: 12px; }
#Root, #MainContent, #PageScrollArea, QStackedWidget { background-color: #0B111B; }
#Sidebar { background-color: #0D1521; border-right: 1px solid #1D2A39; }
#Logo { background-color: #57E0C0; color: #09201E; font-size: 25px; font-weight: 800;
 border-radius: 15px; min-width: 48px; max-width: 48px; min-height: 48px; max-height: 48px;
 qproperty-alignment: AlignCenter; }
#Brand { color: #F1F5F9; font-size: 16px; font-weight: 800; letter-spacing: 2px; }
#BrandSubtitle, #SidebarFooter { color: #8290A2; font-size: 10px; }
#NavSection, #WorkspaceLabel { color: #8494A9; font-size: 10px; font-weight: 700; letter-spacing: 1.5px; }
#PageTitle { color: #F1F5F9; font-size: 27px; font-weight: 700; }
#PageDescription { color: #9BAABD; font-size: 12px; }
#Hero { background-color: #111F2D; border: 1px solid #21374A; border-radius: 15px; }
#Eyebrow { color: #57D9BC; font-size: 10px; font-weight: 700; letter-spacing: 1.6px; }
#HeroTitle { color: #F3F7FB; font-size: 21px; font-weight: 700; }
#HeroDescription, #NoticeText { color: #A8B6C7; }
#ReadOnlyBadge { background-color: #12362F; color: #73E3C8; border: 1px solid #1E5449;
 border-radius: 9px; padding: 9px 11px; font-size: 9px; font-weight: 700; letter-spacing: 1px; }
#InfoCard, #Notice { background-color: #101A27; border: 1px solid #202E3E; border-radius: 12px; }
#InfoCard:hover { border-color: #31485A; }
#CardHeading { color: #8E9DB0; font-size: 9px; font-weight: 700; letter-spacing: 1.3px; }
#CardValue { color: #EAF0F7; font-size: 16px; font-weight: 700; }
#MutedText { color: #95A4B7; }
#SectionTitle { color: #EAF0F7; font-size: 17px; font-weight: 700; }
#StatusIndicator { min-width: 8px; max-width: 8px; min-height: 8px; max-height: 8px;
 border-radius: 4px; background-color: #718198; }
#StatusIndicator[tone="good"] { background-color: #55D6B2; }
#StatusIndicator[tone="warning"] { background-color: #E9B96E; }
#StatusIndicator[tone="bad"] { background-color: #F07878; }
#StatusIndicator[tone="neutral"] { background-color: #718198; }
#NavigationButton { background: transparent; color: #A5B2C3; text-align: left; padding: 10px 11px;
 border: 1px solid transparent; border-radius: 8px; font-weight: 600; }
#NavigationButton:hover { background-color: #152231; color: #F2F6FB; }
#NavigationButton:checked { background-color: #15322F; color: #75E3CA; border-color: #204B43; }
#SidebarFooterPanel { background-color: #111C29; border: 1px solid #223143; border-radius: 10px; }
#SidebarMode { color: #60D9BA; font-size: 9px; font-weight: 700; letter-spacing: 1px; }
#SupportBadge { background-color: #182839; color: #9BB0C3; border: 1px solid #2B4053;
 border-radius: 7px; padding: 6px 8px; font-size: 9px; font-weight: 700; }
#PrimaryButton, #SecondaryButton, #ConnectButton {
 background-color: #2CB99A; color: #061D1A; border: none; border-radius: 8px;
 padding: 9px 16px; font-weight: 700; }
#PrimaryButton:hover, #ConnectButton:hover { background-color: #49D2B0; }
#SecondaryButton { background-color: #1B2A38; color: #DCE7F1; border: 1px solid #304357; }
#SecondaryButton:hover { background-color: #26394A; }
#PrimaryButton:disabled, #ConnectButton:disabled { background-color: #263D3A; color: #91A9A3; }
#ConnectButton { font-size: 15px; padding: 13px 22px; }
#ConnectButton[state="connected"] { background-color: #E08080; color: #2B1010; }
#ConnectButton[state="error"] { background-color: #E9B96E; color: #241A08; }
#PageScrollArea { background: transparent; border: none; }
#Console { background-color: #0D1723; border: 1px solid #223246; border-radius: 10px;
 padding: 12px; color: #C3D0DE; selection-background-color: #245A54;
 font-family: monospace; font-size: 11px; }
#SearchField, QComboBox, QLineEdit { background-color: #0D1723; color: #E7EDF6;
 border: 1px solid #2B3D50; border-radius: 8px; padding: 9px; }
#CountryList { background-color: #101A27; border: 1px solid #202E3E; border-radius: 10px;
 padding: 4px; outline: none; }
#CountryList::item { padding: 12px; border-radius: 6px; }
#CountryList::item:selected, #CountryList::item:hover { background-color: #17352F; color: #78E0C8; }
#AvailabilityLabel[tone="good"] { color: #68DDBD; }
#AvailabilityLabel[tone="bad"] { color: #F28A8A; }
#AvailabilityLabel[tone="neutral"] { color: #E9B96E; }
#ConnectionStatus { font-size: 22px; font-weight: 700; }
#ConnectionStatus[tone="good"] { color: #68DDBD; }
#ConnectionStatus[tone="bad"] { color: #F28A8A; }
#ConnectionStatus[tone="neutral"] { color: #C6D1DD; }
#ConnectionProgress { min-height: 11px; max-height: 11px; border: 0;
 border-radius: 5px; background-color: #1A2938; text-align: center; }
#ConnectionProgress::chunk { background-color: #43C6A7; border-radius: 5px; }
QScrollBar:vertical { background: transparent; width: 9px; margin: 3px; }
QScrollBar::handle:vertical { background: #304357; min-height: 30px; border-radius: 4px; }
QScrollBar::handle:vertical:hover { background: #47627A; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; border: none; }
"""


LIGHT_THEME = """
QWidget { color: #253448; font-family: Arial; font-size: 12px; }
#Root, #MainContent, #PageScrollArea, QStackedWidget { background-color: #F3F6FA; }
#Sidebar { background-color: #FFFFFF; border-right: 1px solid #DCE3EB; }
#Logo { background-color: #27B596; color: #FFFFFF; font-size: 25px; font-weight: 800;
 border-radius: 15px; min-width: 48px; max-width: 48px; min-height: 48px; max-height: 48px;
 qproperty-alignment: AlignCenter; }
#Brand { color: #1B2A3A; font-size: 16px; font-weight: 800; letter-spacing: 2px; }
#BrandSubtitle, #SidebarFooter, #MutedText { color: #68798B; font-size: 10px; }
#NavSection, #WorkspaceLabel { color: #748396; font-size: 10px; font-weight: 700; letter-spacing: 1.5px; }
#PageTitle { color: #1B2A3A; font-size: 27px; font-weight: 700; }
#PageDescription { color: #5D6E80; font-size: 12px; }
#Hero { background-color: #FFFFFF; border: 1px solid #DCE5EC; border-radius: 15px; }
#Eyebrow { color: #16866E; font-size: 10px; font-weight: 700; letter-spacing: 1.6px; }
#HeroTitle, #SectionTitle { color: #1D2B3B; font-size: 19px; font-weight: 700; }
#HeroDescription { color: #5D6E80; }
#InfoCard, #Notice { background-color: #FFFFFF; border: 1px solid #DFE6ED; border-radius: 12px; }
#CardHeading { color: #68798B; font-size: 9px; font-weight: 700; letter-spacing: 1.3px; }
#CardValue { color: #243447; font-size: 16px; font-weight: 700; }
#StatusIndicator { min-width: 8px; max-width: 8px; min-height: 8px; max-height: 8px; border-radius: 4px; background-color: #8492A1; }
#StatusIndicator[tone="good"] { background-color: #159B7C; }
#StatusIndicator[tone="warning"] { background-color: #C5851E; }
#StatusIndicator[tone="bad"] { background-color: #D04F4F; }
#NavigationButton { background: transparent; color: #55687A; text-align: left; padding: 10px 11px;
 border: 1px solid transparent; border-radius: 8px; font-weight: 600; }
#NavigationButton:hover { background-color: #F0F5F7; color: #243447; }
#NavigationButton:checked { background-color: #E2F4EF; color: #14785F; border-color: #C5E8DE; }
#SidebarFooterPanel { background-color: #F7F9FB; border: 1px solid #DFE6ED; border-radius: 10px; }
#SidebarMode { color: #16866E; font-size: 9px; font-weight: 700; letter-spacing: 1px; }
#PrimaryButton, #ConnectButton { background-color: #25A987; color: #FFFFFF; border: none;
 border-radius: 8px; padding: 9px 16px; font-weight: 700; }
#ConnectButton { font-size: 15px; padding: 13px 22px; }
#SecondaryButton { background-color: #F2F5F8; color: #32465A; border: 1px solid #D7E0E8;
 border-radius: 8px; padding: 9px 16px; font-weight: 700; }
#PageScrollArea { background: transparent; border: none; }
#Console { background-color: #FFFFFF; border: 1px solid #D8E1E9; border-radius: 10px;
 padding: 12px; color: #26384B; font-family: monospace; font-size: 11px; }
#SearchField, QComboBox, QLineEdit { background-color: #FFFFFF; color: #253448;
 border: 1px solid #CDD8E2; border-radius: 8px; padding: 9px; }
#CountryList { background-color: #FFFFFF; border: 1px solid #DCE3EB; border-radius: 10px; padding: 4px; }
#CountryList::item { padding: 12px; border-radius: 6px; }
#CountryList::item:selected, #CountryList::item:hover { background-color: #E2F4EF; color: #14785F; }
#ConnectionStatus { font-size: 22px; font-weight: 700; }
#ConnectionStatus[tone="good"] { color: #16866E; }
#ConnectionStatus[tone="bad"] { color: #D04F4F; }
#ConnectionProgress { min-height: 11px; max-height: 11px; border: 0; border-radius: 5px; background-color: #E4EBF0; }
#ConnectionProgress::chunk { background-color: #25A987; border-radius: 5px; }
"""


def stylesheet(name: str) -> str:
    return LIGHT_THEME if name == "light" else DARK_THEME
