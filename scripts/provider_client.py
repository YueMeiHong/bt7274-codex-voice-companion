# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (c) 2026 BT-7274 Voice Companion contributors

"""Direct requests from this computer to the user's selected provider."""
import httpx

class ProviderError(RuntimeError):
    pass

async def complete(client,profile,messages,max_tokens=220):
    if not profile['model'].strip():raise ProviderError('请先填写模型名称')
    if profile.get('provider') in {'deepseek','openai'} and not profile['api_key']:
        raise ProviderError('请先填写当前服务商的 API Key')
    headers={}
    if profile['api_key']:headers['Authorization']='Bearer '+profile['api_key']
    payload={'model':profile['model'],'messages':messages,'max_tokens':max_tokens,'stream':False}
    if profile.get('provider')=='deepseek':payload['thinking']={'type':'disabled'}
    try:
        response=await client.post(profile['base_url'].rstrip('/')+'/chat/completions',headers=headers,json=payload)
        if response.status_code in {401,403}:raise ProviderError('认证失败：请检查当前服务商的 API Key 或权限')
        if response.status_code==404:raise ProviderError('未找到接口或模型：请检查 API 地址与模型名称')
        if response.status_code==429:raise ProviderError('请求受限：请检查额度或稍后重试')
        if response.is_error:raise ProviderError('服务商请求失败（HTTP '+str(response.status_code)+'）')
        result=response.json()['choices'][0]['message']['content']
        if not isinstance(result,str) or not result.strip():raise ValueError('empty content')
        return result.strip()
    except httpx.TimeoutException as exc:raise ProviderError('连接超时：请检查服务地址和本机网络') from exc
    except httpx.RequestError as exc:raise ProviderError('无法连接：请检查服务地址，使用 Ollama 时确认它已启动') from exc
    except (KeyError,ValueError,TypeError,IndexError) as exc:raise ProviderError('服务返回格式不兼容：需要 OpenAI 兼容聊天接口') from exc

async def test_connection(profile):
    async with httpx.AsyncClient(timeout=20) as client:
        await complete(client,profile,[{'role':'user','content':'Reply only OK.'}],max_tokens=8)
    return '连接成功，当前模型已返回测试回复。'
