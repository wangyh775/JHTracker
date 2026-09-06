import pytest
from src.services.resume_parser import parse_resume_content, extract_skills_from_text

def test_extract_skills():
    text = "Proficient in Python and TypeScript, familiar with React, FastAPI and Docker, using Git and Redis"
    skills = extract_skills_from_text(text)
    assert 'Python' in skills
    assert 'TypeScript' in skills
    assert 'React' in skills
    assert 'FastAPI' in skills
    assert 'Docker' in skills
    assert 'Git' in skills
    assert 'Redis' in skills

def test_parse_markdown_resume():
    content = b"# Alice - Software Engineer\n\n## Skills\n- Python, FastAPI, Docker, PostgreSQL"
    title, content_md, skills = parse_resume_content('resume.md', content)
    assert 'Python' in skills
    assert 'FastAPI' in skills
    assert len(content_md) > 0

def test_parse_txt_resume():
    content = b"Bob Resume\nSkills: Java, Spring Boot, MySQL"
    title, content_md, skills = parse_resume_content('resume.txt', content)
    assert 'Java' in skills
    assert 'Spring Boot' in skills
    assert 'MySQL' in skills
    assert '# ' in content_md
