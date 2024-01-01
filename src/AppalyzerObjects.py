import dataclasses

@dataclasses.dataclass
class RegEx_Match_Position:
    '''
    Star and End position of match
    '''
    start: int
    end: int


@dataclasses.dataclass
class RegEx_Match:
    '''
    Regex Match
    '''
    rel_path: str
    line_match: str
    regex_match: str
    match_pos: RegEx_Match_Position

@dataclasses.dataclass
class FileObj:
    '''
    File information for the match
    '''
    file_path: str
    file_contents: str
    matches: list[RegEx_Match]

