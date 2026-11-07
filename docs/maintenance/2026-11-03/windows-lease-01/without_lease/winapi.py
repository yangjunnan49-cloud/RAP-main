"""Public Windows memory counters; no WMI, WSL or elevated service access."""
import ctypes,time
from ctypes import wintypes
class Performance(ctypes.Structure):
    _fields_=[('cb',wintypes.DWORD)]+[(n,ctypes.c_size_t) for n in ('CommitTotal','CommitLimit','CommitPeak','PhysicalTotal','PhysicalAvailable','SystemCache','KernelTotal','KernelPaged','KernelNonpaged','PageSize')]+[(n,wintypes.DWORD) for n in ('HandleCount','ProcessCount','ThreadCount')]
class ProcessMemory(ctypes.Structure):
    _fields_=[('cb',wintypes.DWORD),('PageFaultCount',wintypes.DWORD)]+[(n,ctypes.c_size_t) for n in ('PeakWorkingSetSize','WorkingSetSize','QuotaPeakPagedPoolUsage','QuotaPagedPoolUsage','QuotaPeakNonPagedPoolUsage','QuotaNonPagedPoolUsage','PagefileUsage','PeakPagefileUsage')]
psapi=ctypes.WinDLL('psapi',use_last_error=True);kernel=ctypes.WinDLL('kernel32',use_last_error=True)
psapi.GetPerformanceInfo.argtypes=[ctypes.POINTER(Performance),wintypes.DWORD];psapi.GetProcessMemoryInfo.argtypes=[wintypes.HANDLE,ctypes.POINTER(ProcessMemory),wintypes.DWORD]
kernel.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD];kernel.OpenProcess.restype=wintypes.HANDLE;kernel.GetCurrentProcess.restype=wintypes.HANDLE;kernel.CloseHandle.argtypes=[wintypes.HANDLE]
def memory():
    start=time.monotonic();p=Performance();p.cb=ctypes.sizeof(p);assert psapi.GetPerformanceInfo(ctypes.byref(p),p.cb),ctypes.get_last_error()
    return dict(headroom_bytes=int((p.CommitLimit-p.CommitTotal)*p.PageSize),query_seconds=time.monotonic()-start,page_size=int(p.PageSize),commit_total_pages=int(p.CommitTotal),commit_limit_pages=int(p.CommitLimit),api='GetPerformanceInfo')
def peak(handle=None):
    p=ProcessMemory();p.cb=ctypes.sizeof(p);handle=kernel.GetCurrentProcess() if handle is None else handle
    assert psapi.GetProcessMemoryInfo(handle,ctypes.byref(p),p.cb),ctypes.get_last_error()
    return int(p.PeakWorkingSetSize)
