import yaml
import time
import sys
from rich.console import Console
from typing import Dict, Any, List
from cli.models import AnalystType
from cli.main import run_analysis

console = Console()

class RateLimitError(Exception):
    """自定义API限制异常"""
    pass

def execute_job(job_config: Dict[str, Any]) -> bool:
    """执行单个交易分析任务"""
    job_id = job_config.get('job_id', '未命名任务')
    ticker = job_config['ticker']
    date = job_config['date']
    
    console.print(f"\n[bold cyan]🚀 开始任务: {job_id}[/bold cyan]")
    console.print(f"▷ 股票: {ticker}")
    console.print(f"▷ 日期: {date}")
    console.print(f"▷ 分析模块: {', '.join(job_config['analysts'])}")
    console.print(f"▷ 研究深度: {job_config['research_depth']}")
    
    try:
        start_time = time.time()
        
        # 转换分析师类型为枚举
        analysts = [AnalystType(a) for a in job_config['analysts']]
        
        # 调用参数化分析函数
        run_analysis({
            'ticker': ticker,
            'analysis_date': date,
            'analysts': analysts,
            'research_depth': job_config['research_depth'],
            'llm_provider': job_config['llm_provider'],
            'backend_url': job_config['backend_url'],
            'shallow_thinker': job_config['shallow_thinker'],
            'deep_thinker': job_config['deep_thinker'],
            'online_tools': job_config.get('online_tools', True)
        })
        
        elapsed = time.time() - start_time
        console.print(f"[green]✓ 任务 {job_id} 完成 (耗时: {elapsed:.2f}s)[/green]")
        return True
    except RateLimitError:
        console.print("[yellow]⚠️ API限制触发，将在重试后继续[/yellow]")
        raise  # 触发重试机制
    except Exception as e:
        console.print(f"[red]✗ 任务 {job_id} 失败: {str(e)}[/red]")
        return False

def run_jobs(config_path: str, max_retries: int = 3, retry_delay: int = 60):
    """执行配置文件中的所有交易分析任务"""
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
    except Exception as e:
        console.print(f"[red]配置文件读取失败: {str(e)}[/red]")
        return
    
    if not config or 'jobs' not in config:
        console.print("[red]错误: 配置文件格式无效[/red]")
        return
    
    total_jobs = len(config['jobs'])
    console.print(f"[bold]加载到 {total_jobs} 个任务[/bold]")
    
    success_count = 0
    for i, job in enumerate(config['jobs'], 1):
        console.rule(f"[bold]任务 {i}/{total_jobs} ({job.get('job_id', '未命名')})[/bold]")
        
        # 重试机制
        for attempt in range(1, max_retries + 1):
            try:
                if attempt > 1:
                    console.print(f"🔄 重试 {attempt}/{max_retries} (等待{retry_delay}秒)...")
                    time.sleep(retry_delay)
                
                if execute_job(job):
                    success_count += 1
                    break
            except RateLimitError:
                if attempt == max_retries:
                    console.print(f"[red]✗ 任务 {job.get('job_id')} 超过最大重试次数[/red]")
            except Exception:
                if attempt == max_retries:
                    console.print(f"[red]✗ 任务 {job.get('job_id')} 最终失败[/red]")
    
    console.print(f"\n[bold]任务完成汇总:[/bold] {success_count} 成功, {total_jobs-success_count} 失败")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        console.print("用法: python -m cli.job_runner <配置文件路径>")
        console.print("示例: python -m cli.job_runner config/trading_jobs.yaml")
        sys.exit(1)
    
    run_jobs(sys.argv[1])
