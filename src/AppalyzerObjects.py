"""Module of DataClasses used in Appalyzer"""
import dataclasses

@dataclasses.dataclass
class RegExMatchPosition:
    '''
    Star and End position of match
    '''
    start: int
    end: int


@dataclasses.dataclass
class RegExMatch:
    '''
    Regex Match
    '''
    rel_path: str
    line_match: str
    regex_match: str
    match_pos: RegExMatchPosition

@dataclasses.dataclass
class FileObj:
    '''
    File information for the match
    '''
    file_path: str
    file_contents: str
    matches: list[RegExMatch]
