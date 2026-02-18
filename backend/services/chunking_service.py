import re
from typing import List, Dict, Any
from dataclasses import dataclass

@dataclass
class Chunk:
    text: str
    metadata: Dict[str, Any]

class RecursiveMarkdownSplitter:
    """recursive markdown splitter respecting headers and structure"""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split_text(self, text: str) -> List[Chunk]:
        """split text into chunks preserving hierarchy"""
        # 1. logical split by headers
        sections = self._split_by_headers(text)
        
        final_chunks = []
        for section in sections:
            # 2. keep small sections valid
            if len(section['text']) <= self.chunk_size:
                final_chunks.append(Chunk(
                    text=section['text'], 
                    metadata=section['metadata']
                ))
            else:
                # 3. recursive split for large sections
                sub_chunks = self._recursive_split(
                    section['text'], 
                    section['metadata']
                )
                final_chunks.extend(sub_chunks)
                
        return final_chunks

    def _split_by_headers(self, text: str) -> List[Dict[str, Any]]:
        """parse content into sections based on markdown headers"""
        lines = text.split('\n')
        sections = []
        current_headers = [] 
        current_buffer = []
        
        for line in lines:
            header_match = re.match(r'^(#{1,6})\s+(.+)$', line)
            
            if header_match:
                # flush buffer with previous context
                if current_buffer:
                    content = '\n'.join(current_buffer).strip()
                    if content:
                        sections.append({
                            'text': content,
                            'metadata': {'headers': list(current_headers)}
                        })
                    current_buffer = []
                
                # update header context
                level = len(header_match.group(1))
                title = header_match.group(2).strip()
                
                # maintain hierarchy: truncate deeper levels
                if len(current_headers) >= level:
                    current_headers = current_headers[:level-1]
                
                current_headers.append(title)
                current_buffer.append(line)
            else:
                current_buffer.append(line)
        
        # flush remaining
        if current_buffer:
            content = '\n'.join(current_buffer).strip()
            if content:
                sections.append({
                    'text': content,
                    'metadata': {'headers': list(current_headers)}
                })
                
        return sections

    def _recursive_split(self, text: str, metadata: Dict[str, Any]) -> List[Chunk]:
        """split large text blocks by paragraph then sentence"""
        chunks = []
        paragraphs = re.split(r'\n\n+', text)
        
        current_chunk = []
        current_len = 0
        
        for para in paragraphs:
            para_len = len(para)
            
            # handle massive paragraphs
            if para_len > self.chunk_size:
                # flush existing
                if current_chunk:
                    chunks.append(Chunk(
                        text='\n\n'.join(current_chunk),
                        metadata=metadata
                    ))
                    current_chunk = []
                    current_len = 0
                
                # split by sentence
                sentences = re.split(r'(?<=[.!?])\s+', para)
                sent_buffer = []
                sent_len = 0
                
                for sent in sentences:
                    if sent_len + len(sent) > self.chunk_size:
                        if sent_buffer:
                            chunks.append(Chunk(
                                text=' '.join(sent_buffer),
                                metadata=metadata
                            ))
                        sent_buffer = [sent]
                        sent_len = len(sent)
                    else:
                        sent_buffer.append(sent)
                        sent_len += len(sent)
                
                if sent_buffer:
                    chunks.append(Chunk(
                        text=' '.join(sent_buffer),
                        metadata=metadata
                    ))
            
            # aggregate normal paragraphs
            elif current_len + para_len + 2 > self.chunk_size:
                chunks.append(Chunk(
                    text='\n\n'.join(current_chunk),
                    metadata=metadata
                ))
                current_chunk = [para]
                current_len = para_len
            else:
                current_chunk.append(para)
                current_len += para_len + 2
        
        # final flush
        if current_chunk:
            chunks.append(Chunk(
                text='\n\n'.join(current_chunk),
                metadata=metadata
            ))
            
        return chunks
