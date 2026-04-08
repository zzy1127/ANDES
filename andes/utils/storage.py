from abc import ABC, abstractmethod
import atexit
import signal
import tempfile
import weakref

from andes import get_logger
import pandas as pd
import json
from typing import Any, Dict, Literal, Generator
import os
import copy

class DataFlowStorage(ABC):
    """
    Abstract base class for data storage.
    """
    @abstractmethod
    def get_keys_from_dataframe(self) -> list[str]:
        """
        Get keys from the dataframe stored in the storage.
        This method should be implemented by subclasses to extract keys from the data.
        """
        pass
    @abstractmethod
    def read(self, output_type) -> Any:
        """
        Read data from file.
        type: type that you want to read to, such as "datatrame", List[dict], etc.
        """
        pass
    
    @abstractmethod
    def write(self, data: Any) -> Any:
        pass

# --- 新增的 __repr__ 方法 ---
    def __repr__(self):
        """
        返回一个表示该对象所有成员变量及其键值对的字符串。
        """
        # 获取实例的所有属性（成员变量）
        attrs = self.__dict__
        
        # 格式化键值对列表
        attr_strs = []
        for key, value in attrs.items():
            # 特殊处理 pandas DataFrame 或其他大型对象
            if isinstance(value, pd.DataFrame):
                # 如果是 DataFrame，只显示其类型和形状，避免输出过多内容
                value_repr = f"<DataFrame shape={value.shape}>"
            elif isinstance(value, set):
                # 简化集合的显示
                 value_repr = f"<{type(value).__name__} size={len(value)}>"
            elif isinstance(value, dict):
                # 简化字典的显示
                 value_repr = f"<{type(value).__name__} size={len(value)}>"
            else:
                # 使用标准的 repr() 获取值表示，并限制长度
                value_repr = repr(value)
                if len(value_repr) > 100:  # 限制长度以避免超长输出
                    value_repr = value_repr[:97] + "..."
                    
            attr_strs.append(f"  {key} = {value_repr}")
            
        # 构造最终的字符串
        body = "\n".join(attr_strs)
        return f"<{self.__class__.__name__} Object:\n{body}\n>"
    # ---------------------------
class FileStorage(DataFlowStorage):
    """
    Storage for file system.
    """
    def __init__(
        self, 
        first_entry_file_name: str,
        cache_path:str="./cache",
        file_name_prefix:str="andes_cache_step",
        cache_type:Literal["json", "jsonl", "csv", "parquet", "pickle"] = "jsonl"
    ):
        """
        Initialize a FileStorage.

        FileStorage is a disk-backed storage implementation that reads from and
        writes to the local filesystem on every read/write operation. Unlike
        LazyFileStorage, data is persisted immediately and no in-memory buffering
        is maintained across steps.

        The storage follows a step-based access pattern compatible with
        DataFlowStorage. Step 0 (the "first entry") can be loaded from:
        - a local file path, or
        - a remote dataset specified with the "hf:" (HuggingFace) or "ms:"
        (ModelScope) prefix.

        Subsequent steps are materialized as files on disk under `cache_path`,
        with filenames derived from `file_name_prefix`, the step index, and
        `cache_type`.

        Args:
            first_entry_file_name (str):
                Path or source identifier used as the data source for step 0.
                - "hf:{dataset}[:config][:split]" loads a HuggingFace dataset.
                - "ms:{dataset}[:split]" loads a ModelScope dataset.
                - Otherwise, this is treated as a local file path, and the file
                extension determines how it is read.
            cache_path (str, optional):
                Directory where cache files for steps >= 1 are stored.
                Defaults to "./cache".
            file_name_prefix (str, optional):
                Prefix used when generating filenames for cached steps.
                Cache files are named as
                "{file_name_prefix}_step{n}.{cache_type}".
                Defaults to "andes_cache_step".
            cache_type (Literal["json","jsonl","csv","parquet","pickle"], optional):
                File format used when writing step outputs to disk.
                Defaults to "jsonl".

        Returns:
            None

        Notes:
            - The internal `operator_step` counter starts at -1 and is incremented
            by calling `step()`.
            - Calling `write(...)` writes data immediately to disk for
            `operator_step + 1`.
            - No atomic-write or buffering guarantees are provided beyond the
            underlying pandas file writers.
            - This class is simpler but less fault-tolerant than LazyFileStorage,
            as partially written files may exist if a process is interrupted.
        """
        self.first_entry_file_name = first_entry_file_name
        self.cache_path = cache_path
        self.file_name_prefix = file_name_prefix
        self.cache_type = cache_type
        self.operator_step = -1
        self.logger = get_logger()

    def _get_cache_file_path(self, step) -> str:
        if step == -1:
            self.logger.error("You must call storage.step() before reading or writing data. Please call storage.step() first for each operator step.")  
            raise ValueError("You must call storage.step() before reading or writing data. Please call storage.step() first for each operator step.")
        if step == 0:
            # If it's the first step, use the first entry file name
            return os.path.join(self.first_entry_file_name)
        else:
            return os.path.join(self.cache_path, f"{self.file_name_prefix}_step{step}.{self.cache_type}")

    def step(self):
        self.operator_step += 1
        return copy.copy(self) # TODO if future maintain an object in memory, we need to apply a deepcopy (except the dataframe object during copy to avoid OOM)
    
    def reset(self):
        self.operator_step = -1
        return self
    
    def get_keys_from_dataframe(self) -> list[str]:
        dataframe = self.read(output_type="dataframe")
        return dataframe.columns.tolist() if isinstance(dataframe, pd.DataFrame) else []
    
    def _load_local_file(self, file_path: str, file_type: str) -> pd.DataFrame:
        """Load data from local file based on file type."""
        # check if file exists
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File {file_path} does not exist. Please check the path.")
        # Load file based on type
        try:
            if file_type == "json":
                return pd.read_json(file_path)
            elif file_type == "jsonl":
                return pd.read_json(file_path, lines=True)
            elif file_type == "csv":
                return pd.read_csv(file_path)
            elif file_type == "parquet":
                return pd.read_parquet(file_path)
            elif file_type == "pickle":
                return pd.read_pickle(file_path)
            elif self.cache_type == "xlsx":
                return pd.read_excel(file_path)
            else:
                raise ValueError(f"Unsupported file type: {file_type}")
        except Exception as e:
            raise ValueError(f"Failed to load {file_type} file: {str(e)}")
    
    def _convert_output(self, dataframe: pd.DataFrame, output_type: str) -> Any:
        """Convert dataframe to requested output type."""
        if output_type == "dataframe":
            return dataframe
        elif output_type == "dict":
            return dataframe.to_dict(orient="records")
        raise ValueError(f"Unsupported output type: {output_type}")

    def read(self, output_type: Literal["dataframe", "dict"]="dataframe") -> Any:
        """
        Read data from current file managed by storage.
        
        Args:
            output_type: Type that you want to read to, either "dataframe" or "dict".
            Also supports remote datasets with prefix:
                - "hf:{dataset_name}{:config}{:split}"  => HuggingFace dataset eg. "hf:openai/gsm8k:main:train"
                - "ms:{dataset_name}{}:split}"          => ModelScope dataset eg. "ms:modelscope/gsm8k:train"
        
        Returns:
            Depending on output_type:
            - "dataframe": pandas DataFrame
            - "dict": List of dictionaries
        
        Raises:
            ValueError: For unsupported file types or output types
        """
        if self.operator_step == 0 and self.first_entry_file_name == "":
            self.logger.info("first_entry_file_name is empty, returning empty dataframe")
            empty_dataframe = pd.DataFrame()
            return self._convert_output(empty_dataframe, output_type)

        file_path = self._get_cache_file_path(self.operator_step)
        self.logger.info(f"Reading data from {file_path} with type {output_type}")

        if self.operator_step == 0:
            source = self.first_entry_file_name
            self.logger.info(f"Reading remote dataset from {source} with type {output_type}")
            if source.startswith("hf:"):
                from datasets import load_dataset
                _, dataset_name, *parts = source.split(":")

                if len(parts) == 1:
                    config, split = None, parts[0]
                elif len(parts) == 2:
                    config, split = parts
                else:
                    config, split = None, "train"

                dataset = (
                    load_dataset(dataset_name, config, split=split) 
                    if config 
                    else load_dataset(dataset_name, split=split)
                )
                dataframe = dataset.to_pandas()
                return self._convert_output(dataframe, output_type)
        
            elif source.startswith("ms:"):
                from modelscope import MsDataset
                _, dataset_name, *split_parts = source.split(":")
                split = split_parts[0] if split_parts else "train"

                dataset = MsDataset.load(dataset_name, split=split)
                dataframe = pd.DataFrame(dataset)
                return self._convert_output(dataframe, output_type)
                            
            else:
                local_cache = file_path.split(".")[-1]
        else:
            local_cache = self.cache_type

        dataframe = self._load_local_file(file_path, local_cache)
        return self._convert_output(dataframe, output_type)
        
    def write(self, data: Any) -> Any:
        """
        Write data to current file managed by storage.
        data: Any, the data to write, it should be a dataframe, List[dict], etc.
        """
        def clean_surrogates(obj):
            """递归清理数据中的无效Unicode代理对字符"""
            if isinstance(obj, str):
                # 替换无效的Unicode代理对字符（如\udc00）
                return obj.encode('utf-8', 'replace').decode('utf-8')
            elif isinstance(obj, dict):
                return {k: clean_surrogates(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [clean_surrogates(item) for item in obj]
            elif isinstance(obj, (int, float, bool)) or obj is None:
                # 数字、布尔值和None直接返回
                return obj
            else:
                # 其他类型（如自定义对象）尝试转为字符串处理
                try:
                    return clean_surrogates(str(obj))
                except Exception:
                    # 如果转换失败，返回原对象或空字符串（根据需求选择）
                    return obj

        # 转换数据为DataFrame
        if isinstance(data, list):
            if len(data) > 0 and isinstance(data[0], dict):
                # 清洗列表中的每个字典
                cleaned_data = [clean_surrogates(item) for item in data]
                dataframe = pd.DataFrame(cleaned_data)
            else:
                raise ValueError(f"Unsupported data type: {type(data[0])}")
        elif isinstance(data, pd.DataFrame):
            # 对DataFrame的每个元素进行清洗
            dataframe = data.map(clean_surrogates)
        else:
            raise ValueError(f"Unsupported data type: {type(data)}")

        # if type(data) == list:
        #     if type(data[0]) == dict:
        #         dataframe = pd.DataFrame(data)
        #     else:
        #         raise ValueError(f"Unsupported data type: {type(data[0])}")
        # elif type(data) == pd.DataFrame:
        #     dataframe = data
        # else:
        #     raise ValueError(f"Unsupported data type: {type(data)}")

        file_path = self._get_cache_file_path(self.operator_step + 1)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        self.logger.success(f"Writing data to {file_path} with type {self.cache_type}")
        if self.cache_type == "json":
            dataframe.to_json(file_path, orient="records", force_ascii=False, indent=2)
        elif self.cache_type == "jsonl":
            dataframe.to_json(file_path, orient="records", lines=True, force_ascii=False)
        elif self.cache_type == "csv":
            dataframe.to_csv(file_path, index=False)
        elif self.cache_type == "parquet":
            dataframe.to_parquet(file_path)
        elif self.cache_type == "pickle":
            dataframe.to_pickle(file_path)
        elif self.cache_type == "xlsx":
            dataframe.to_excel(file_path, index=False)
        else:
            raise ValueError(f"Unsupported file type: {self.cache_type}, output file should end with json, jsonl, csv, parquet, pickle or xlsx")
        
        return file_path    
