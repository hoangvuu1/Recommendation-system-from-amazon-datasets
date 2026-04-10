"""
Product mapper - maps product IDs to their names and images from meta_ui parquet files
"""
import json
import pickle
from pathlib import Path
from typing import Dict, Optional, Tuple
import pandas as pd

class ProductMapper:
    """Load and cache product names and images from meta_ui parquet files"""
    
    def __init__(self):
        self.product_map: Dict[str, Dict[str, Optional[str]]] = {}  # {item_id: {"title": "...", "image_url": "..."}}
        self.cache_file = None
        self._loaded = False
    
    def load_from_cache(self, cache_file: str) -> Dict[str, str]:
        """Load product names directly from cache file"""
        if self._loaded and self.product_map:
            return self.product_map
        
        cache_path = Path(cache_file)
        
        if not cache_path.exists():
            print(f"[WARN] Cache file not found: {cache_path}")
            self._loaded = True
            return self.product_map
        
        try:
            with open(cache_path, 'rb') as f:
                self.product_map = pickle.load(f)
                self._loaded = True
                print(f"✓ Loaded {len(self.product_map)} product names from cache")
                return self.product_map
        except Exception as e:
            print(f"[ERROR] Failed to load cache: {e}")
            self._loaded = True
            return self.product_map
    
    def load_from_parquet(self, meta_ui_dir: str) -> Dict[str, str]:
        """Load product names from meta_ui parquet files and cache them"""
        if self._loaded and self.product_map:
            return self.product_map
        
        meta_ui_path = Path(meta_ui_dir)
        cache_file = meta_ui_path.parent / "product_names_cache.pkl"
        
        # Try to load from cache first
        if cache_file.exists():
            try:
                with open(cache_file, 'rb') as f:
                    self.product_map = pickle.load(f)
                    self._loaded = True
                    print(f"✓ Loaded {len(self.product_map)} product names from cache")
                    return self.product_map
            except Exception as e:
                print(f"⚠ Cache load failed: {e}")
        
        # Load from parquet files
        if not meta_ui_path.exists():
            print(f"[WARN] Directory not found: {meta_ui_path}")
            self._loaded = True
            return self.product_map
        
        try:
            # Load all parquet files from meta_ui directory
            parquet_files = list(meta_ui_path.glob("part-*.parquet"))
            
            if not parquet_files:
                print(f"[WARN] No parquet files found in {meta_ui_path}")
                self._loaded = True
                return self.product_map
            
            print(f"Found {len(parquet_files)} parquet files in meta_ui")
            
            # Read and combine all parquet files
            dfs = []
            for pf in parquet_files:
                try:
                    df = pd.read_parquet(pf)
                    dfs.append(df)
                except Exception as e:
                    print(f"[WARN] Failed to read {pf.name}: {e}")
                    continue
            
            if not dfs:
                print(f"[ERROR] Could not read any parquet files from {meta_ui_path}")
                self._loaded = True
                return self.product_map
            
            # Combine all dataframes
            meta_df = pd.concat(dfs, ignore_index=True)
            print(f"[OK] Loaded {len(meta_df)} product records from parquet files")
            
            # Build product mapping (assuming columns like 'item_id'/'product_id' and 'title')
            # Try different column name combinations
            item_id_col = None
            title_col = None
            image_col = None
            
            # Find item_id column (try common names)
            for col in ['item_id', 'product_id', 'asin', 'id']:
                if col in meta_df.columns:
                    item_id_col = col
                    break
            
            # Find title column
            for col in ['title', 'name', 'product_name']:
                if col in meta_df.columns:
                    title_col = col
                    break
            
            # Find image column
            for col in ['images', 'image_url', 'image']:
                if col in meta_df.columns:
                    image_col = col
                    break
            
            if not item_id_col or not title_col:
                print(f"[ERROR] Could not find item_id and title columns in parquet. Available columns: {meta_df.columns.tolist()}")
                self._loaded = True
                return self.product_map
            
            # Build the product map with title and image
            for _, row in meta_df.iterrows():
                try:
                    iid = str(row[item_id_col]).strip()
                    ttl = str(row[title_col]).strip()
                    img = None
                    
                    if image_col:
                        img_val = row.get(image_col)
                        if img_val and pd.notna(img_val):
                            img = str(img_val).strip()
                    
                    if iid and ttl and ttl.lower() != 'nan':
                        self.product_map[iid] = {
                            'title': ttl,
                            'image_url': img
                        }
                except:
                    continue
            
            print(f"[OK] Mapped {len(self.product_map)} products")
            
            # Save cache
            try:
                with open(cache_file, 'wb') as f:
                    pickle.dump(self.product_map, f)
                print(f"[OK] Cached product names to {cache_file.name}")
            except Exception as e:
                print(f"⚠ Cache save failed: {e}")
            
            self._loaded = True
            return self.product_map
        
        except Exception as e:
            print(f"[ERROR] Error loading product names from parquet: {e}")
            self._loaded = True
            return self.product_map
    
    def load_from_jsonl(self, jsonl_path: str) -> Dict[str, str]:
        """Fallback: Load product names from JSONL file and cache them"""
        if self._loaded and self.product_map:
            return self.product_map
        
        jsonl_path = Path(jsonl_path)
        cache_file = jsonl_path.parent / "product_names_cache.pkl"
        
        # Try to load from cache first
        if cache_file.exists():
            try:
                with open(cache_file, 'rb') as f:
                    self.product_map = pickle.load(f)
                    self._loaded = True
                    print(f"✓ Loaded {len(self.product_map)} product names from cache")
                    return self.product_map
            except Exception as e:
                print(f"⚠ Cache load failed: {e}")
        
        # Load from JSONL file
        if not jsonl_path.exists():
            print(f"[WARN] File not found: {jsonl_path}")
            self._loaded = True
            return self.product_map
        
        try:
            with open(jsonl_path, 'r', encoding='utf-8') as f:
                count = 0
                for line in f:
                    try:
                        data = json.loads(line.strip())
                        item_id = data.get('item_id')
                        title = data.get('title')
                        if item_id and title:
                            self.product_map[item_id] = title
                            count += 1
                    except json.JSONDecodeError:
                        continue
            
            # Save cache
            try:
                with open(cache_file, 'wb') as f:
                    pickle.dump(self.product_map, f)
                print(f"[OK] Loaded and cached {len(self.product_map)} product names")
            except Exception as e:
                print(f"⚠ Cache save failed: {e}")
            
            self._loaded = True
            return self.product_map
        
        except Exception as e:
            print(f"[ERROR] Error loading product names: {e}")
            self._loaded = True
            return self.product_map
    
    def get_product_name(self, item_id: str) -> Optional[str]:
        """Get product name for item_id, or return placeholder if not found"""
        product_data = self.product_map.get(item_id)
        
        # Handle both dict (new format) and string (old format)
        product_name = None
        if isinstance(product_data, dict):
            product_name = product_data.get('title')
        elif isinstance(product_data, str):
            product_name = product_data
        
        # If product name not found and it's a placeholder ID (Product Bxxxxxx), replace it
        if not product_name and item_id and item_id.startswith('Product B'):
            return "Sản phẩm hiện không còn bày bán"
        
        # If still no name found, return placeholder
        if not product_name and item_id:
            return "Sản phẩm hiện không còn bày bán"
        
        return product_name
    
    def get_product_info(self, item_id: str) -> Dict[str, Optional[str]]:
        """Get product info (title and image_url) for item_id"""
        product_data = self.product_map.get(item_id)
        
        # Handle both dict (new format) and string (old format)
        info = {'title': None, 'image_url': None}
        
        if isinstance(product_data, dict):
            info = {
                'title': product_data.get('title'),
                'image_url': product_data.get('image_url')
            }
        elif isinstance(product_data, str):
            info = {'title': product_data, 'image_url': None}
        
        # Apply placeholder if title not found
        if not info['title']:
            if item_id and item_id.startswith('Product B'):
                info['title'] = "Sản phẩm hiện không còn bày bán"
            elif item_id:
                info['title'] = "Sản phẩm hiện không còn bày bán"
        
        return info
    
    def is_ready(self) -> bool:
        """Check if mapper is loaded and ready"""
        return self._loaded and len(self.product_map) > 0


# Global instance
_mapper = None

def get_product_mapper(meta_ui_dir: str = None) -> ProductMapper:
    """Get or create global product mapper instance"""
    global _mapper
    if _mapper is None:
        _mapper = ProductMapper()
        if meta_ui_dir:
            _mapper.load_from_parquet(meta_ui_dir)
    return _mapper
