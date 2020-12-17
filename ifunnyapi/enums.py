from enum import Enum


class IFChannel(Enum):
    COMMUNITY_COMMERCIALS = "5fd3ea0dc6ff1f1a8008c4cc"
    CYBERPUNK = "5fd9a9533ea93f29fe1af892"
    WTF = "5e28bbc2a264f60031232af1"
    ANIMALS = "5a05c3e640fe2732008b456d"
    GAMES = "5a05c3e640fe2732008b456e"
    COMIC = "5a05c3e640fe2732008b456a"
    CURSED = "5e28bc02a264f60045536fab"
    SPORTS = "5e28bc33a261d0008f3eccc9"
    VIDEO = "5a05c3e640fe2732008b4569"
    IFUNNY_ORIGINALS = "5accedffaeb90000481cda53"
    WHOLESOME_WEDNESDAY = "5b9710bdeb691ec6576b5b61"


class IFPostVisibility(Enum):
    PUBLIC = "public"
    SUBSCRIBERS_ONLY = "subscribers"


class IFReportType(Enum):
    HATE_SPEECH = "hate"
    NUDITY = "nude"
    SPAM = "spam"
    TARGETED_ABUSE = "target"
    THREATS_OF_HARM = "harm"
    BANNER_ISSUES = "banner"  # This may be incorrect
