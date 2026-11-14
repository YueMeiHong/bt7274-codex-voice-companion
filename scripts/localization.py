# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (c) 2026 BT-7274 Voice Companion contributors

"""Localized labels on Codex's existing native controls."""
from copy import deepcopy

CHOICES={'通用':'Default','自定义':'Custom','开启':'On','关闭':'Off',
 '双向语音':'Voice conversation','只播报回复':'Read replies','只通知结果':'Completion alerts',
 '简短':'Short','正常':'Normal','简体中文':'Simplified Chinese','跟随原回复':'Same as original',
 '自定义 OpenAI 兼容':'OpenAI-compatible','Ollama（本机）':'Ollama (local)',
 '自动（中英）':'Automatic (Chinese/English)','中文 BT':'Chinese BT','英文 BT（实验）':'English BT (experimental)',
 '麦克风未开启':'Microphone off',
 '麦克风未开启，或目标会话尚未启用双向语音':'Microphone off, or voice conversation not enabled',
 '正在收音：停顿后转写':'Listening; pause to transcribe',
 '转写完成，等待发送':'Transcription ready to send',
 '转写已发送，继续收音':'Transcription sent; listening',
 '草稿已发送':'Draft sent',
 '会话列表暂不可用；已有独立配置已保留':'Conversation list unavailable; saved settings retained'}
TITLES={
 'connection_test_status':'Connection test result',
 'interface_language':'Settings language','provider':'Summary provider','base_url':'API base URL','api_key':'API key',
 'model':'Model ID','speech_language':'Summary text language','speech_voice':'Speech voice / language',
 'bt_style':'Concise BT-style summary','summary_length':'Summary length','volume':'Default volume (%)',
 'default_mode':'Default conversation mode','auto_send':'Automatically send transcription',
 'microphone_enabled':'Enable this computer\'s microphone','voice_draft':'Transcription draft',
 'voice_status':'Microphone status','selected_conversation':'Conversation (pinned first, then recent)',
 'conversation_status':'Desktop connection status'}
LOCAL_TITLES={'enabled':'Enable BT for this conversation','mode':'Conversation mode',
 'bt_style':'BT-style summary','summary_length':'Summary length','volume_source':'Volume setting',
 'volume':'Volume (%)','auto_send':'Automatically send transcription'}
GROUPS={'摘要模型连接（保存在本机）':'Summary connection (saved locally)',
 '摘要语言':'Summary language','BT 播报（所有会话的默认值）':'Speech defaults',
 '会话默认行为':'Conversation defaults','本机音色试听':'Local voice previews','设置界面 / Settings':'Settings',
 '本机语音输入':'Local voice input','会话列表':'Conversations'}
TOOLS={'bt_test_connection':'Test current connection','bt_send_voice_draft':'Send draft to selected conversation',
 'bt_refresh_voice':'Read latest transcription','bt_stop_voice':'Stop recording and playback',
 'bt_preview_chinese':'Preview Chinese BT','bt_preview_english':'Preview English BT (experimental)'}
DESCRIPTIONS={
 'connection_test_status':'Last test result; changing connection settings requires a new test. The button also shows success or failure; hover for the full result.',
 'provider':'Each provider keeps its own URL, key, and model on this computer.',
 'base_url':'Use the API base URL, without /chat/completions. Local Ollama usually uses http://localhost:11434/v1.',
 'api_key':'Saved as local text on this computer. Local Ollama can leave this empty. Save an empty value to remove the key.',
 'model':'Use the provider\'s exact model ID, or the name of an installed Ollama model.',
 'speech_language':'Controls summary text. The English voice uses a separate pretrained BT community model.',
 'speech_voice':'AI-generated speech, not official recordings. Chinese: MiDd1Eye / Bert-VITS2; English: DJMalachite / Piper. Summary language follows the voice; settings language is independent.',
 'bt_style':'Summarizes final Codex replies only. Codex retains thinking, tools, and execution.',
 'microphone_enabled':'Only sends to the explicitly selected, enabled voice conversation. Turn off auto-send to review drafts.',
 'voice_draft':'Edit this draft, then press Send draft. It is never redirected to another conversation.',
 'selected_conversation':'Lists titles and identifiers only; no conversation content is read for this list.',
 'volume':'Enter a number or use the native arrows. Editing the conversation volume selects Custom.'}

def _choice(value,name):
    if name=='speech_voice':return {'中文':'Chinese','英文':'English','自动（中英）':'Automatic (Chinese/English)'}.get(value,value)
    if name=='selected_conversation' and isinstance(value,str):
        return value.replace('置顶 · ','Pinned · ',1) if value.startswith('置顶 · ') else value.replace('最近 · ','Recent · ',1)
    if name=='default_mode':return {'talk':'Voice conversation','reply':'Read replies','notify':'Completion alerts'}.get(value,value)
    if name=='summary_length':return {'short':'Short','normal':'Normal'}.get(value,value)
    return CHOICES.get(value,value)

def _english(definition,language):
    if language!='English':return definition
    result=deepcopy(definition)
    for name,field in result['schema']['properties'].items():
        suffix=name.split('__')[-1]
        if name.startswith('conversation__'):field['title']=LOCAL_TITLES.get(suffix,field['title'])
        else:field['title']=TITLES.get(name,field.get('title',name))
        field['description']=DESCRIPTIONS.get(name,DESCRIPTIONS.get(suffix,'Default follows the shared setting; explicit values apply only here.' if name.startswith('conversation__') else 'Changes are saved automatically on this computer.'))
        if name=='volume':field['description']='Default playback volume, from 0 to 100 percent.'
        if 'enum' in field:
            field['enum']=[_choice(v,name) for v in field['enum']]
            if name in result['values']:result['values'][name]=_choice(result['values'][name],name)
    for group in result['layout']:
        if not any(i.get('property','').startswith('conversation__') for i in group['items']):group['title']=GROUPS.get(group['title'],group['title'])
        for item in group['items']:
            if item.get('kind')=='tool':
                item['title']=TOOLS.get(item['tool'],item.get('title',item['tool']))
                item.pop('description',None)
    return result

# Translate only schema metadata and declared choices, never user-entered text.
JP={
 'Last test result; changing connection settings requires a new test. The button also shows success or failure; hover for the full result.':'前回の結果です。接続設定を変更したら再テストしてください。ボタンにも成否を表示し、ホバーすると詳細を確認できます。',
 'Connection test result':'接続テストの結果',
 'Microphone off':'マイクは無効です',
 'Microphone off, or voice conversation not enabled':'マイクが無効、または双方向音声が未設定です',
 'Listening; pause to transcribe':'録音中：話し終えると文字起こしします',
 'Transcription ready to send':'文字起こし完了・送信待ち',
 'Transcription sent; listening':'文字起こし送信済み・録音中',
 'Draft sent':'下書き送信済み',
 'Conversation list unavailable; saved settings retained':'会話一覧を取得できません。保存済みの設定は保持されています',
 'Default':'共通設定','Custom':'カスタム','On':'有効','Off':'無効',
 'Voice conversation':'双方向音声','Read replies':'返信を読み上げ','Completion alerts':'完了通知のみ',
 'Short':'短い','Normal':'標準','Simplified Chinese':'簡体字中国語','English':'英語',
 'Chinese':'中国語','Automatic (Chinese/English)':'自動（中国語・英語）',
 'OpenAI-compatible':'OpenAI 互換','Ollama (local)':'Ollama（ローカル）',
 'Settings language':'設定画面の言語','Summary provider':'要約プロバイダー','API base URL':'API ベース URL',
 'API key':'API キー','Model ID':'モデル ID','Speech voice / language':'音声の言語',
 'Concise BT-style summary':'簡潔な BT 風の要約','Summary length':'読み上げの長さ',
 'Default volume (%)':'既定の音量（%）','Default conversation mode':'会話の既定モード',
 'Automatically send transcription':'文字起こしを自動送信','Enable this computer\'s microphone':'この PC のマイクを有効にする',
 'Transcription draft':'文字起こしの下書き','Microphone status':'マイクの状態',
 'Conversation (pinned first, then recent)':'会話（ピン留め・最近の順）','Desktop connection status':'デスクトップ接続状態',
 'Enable BT for this conversation':'この会話で BT を有効にする','Conversation mode':'この会話のモード',
 'BT-style summary':'BT 風の要約','Volume setting':'音量の設定元','Volume (%)':'音量（%）',
 'Summary connection (saved locally)':'要約モデルの接続（この PC に保存）','Speech defaults':'読み上げの共通設定',
 'Conversation defaults':'会話の共通設定','Local voice previews':'ローカル音声の試聴','Settings':'設定',
 'Local voice input':'ローカル音声入力','Conversations':'会話一覧',
 'Test current connection':'接続をテスト','Send draft to selected conversation':'選択した会話に下書きを送信',
 'Read latest transcription':'最新の文字起こしを取得','Stop recording and playback':'録音と読み上げを停止',
 'Preview Chinese BT':'中国語 BT を試聴','Preview English BT (experimental)':'英語 BT を試聴',
 'Each provider keeps its own URL, key, and model on this computer.':'プロバイダーごとの URL・キー・モデルをこの PC に保存します。',
 'Use the API base URL, without /chat/completions. Local Ollama usually uses http://localhost:11434/v1.':'/chat/completions を除いた URL を入力します。ローカル Ollama は通常 http://localhost:11434/v1 です。',
 'Saved as local text on this computer. Local Ollama can leave this empty. Save an empty value to remove the key.':'キーはこの PC にテキストで保存されます。ローカル Ollama では空欄にできます。空欄で保存するとキーを削除します。',
 'Use the provider\'s exact model ID, or the name of an installed Ollama model.':'プロバイダーのモデル ID、またはインストール済みの Ollama モデル名を入力します。',
 'AI-generated speech, not official recordings. Chinese: MiDd1Eye / Bert-VITS2; English: DJMalachite / Piper. Summary language follows the voice; settings language is independent.':'中国語と英語はそれぞれ独立したローカル BT モデルを使用します。要約の言語は設定画面ではなく音声の言語に従います。',
 'Summarizes final Codex replies only. Codex retains thinking, tools, and execution.':'Codex の最終回答のみを要約します。思考・ツール・実行は Codex が担当します。',
 'Only sends to the explicitly selected, enabled voice conversation. Turn off auto-send to review drafts.':'選択して有効にした音声会話にのみ送信します。下書きを確認する場合は自動送信を無効にしてください。',
 'Edit this draft, then press Send draft. It is never redirected to another conversation.':'下書きを編集して送信してください。別の会話へ自動的に転送されることはありません。',
 'Lists titles and identifiers only; no conversation content is read for this list.':'一覧にはタイトルと識別子のみを取得します。会話の本文は読み取りません。',
 'Enter a number or use the native arrows. Editing the conversation volume selects Custom.':'数値を入力するか矢印で変更します。この会話の音量を編集するとカスタムになります。',
 'Default playback volume, from 0 to 100 percent.':'既定の読み上げ音量（0～100%）です。',
 'Default follows the shared setting; explicit values apply only here.':'共通設定に従うか、この会話専用の値を選択します。',
 'Changes are saved automatically on this computer.':'変更はこの PC に自動保存されます。'
}
JP_REVERSE={v:k for k,v in JP.items()}

def localize(definition,language):
    result=_english(definition,'English') if language=='日本語' else _english(definition,language)
    if language!='日本語':return result
    for name,field in result['schema']['properties'].items():
        for key in ('title','description'):
            if key in field:field[key]=JP.get(field[key],field[key])
        if 'enum' in field:
            # Keep conversation titles untouched; only the list prefix is localized.
            translate=(lambda v:v.replace('Pinned · ','ピン留め · ',1).replace('Recent · ','最近 · ',1)) if name=='selected_conversation' else (lambda v:JP.get(v,v))
            field['enum']=[translate(v) for v in field['enum']]
            if name in result['values']:result['values'][name]=translate(result['values'][name])
    for group in result['layout']:
        if not any(i.get('property','').startswith('conversation__') for i in group['items']):group['title']=JP.get(group['title'],group['title'])
        for item in group['items']:
            if item.get('kind')=='tool':item['title']=JP.get(item['title'],item['title'])
    return result

def normalize_changes(changes):
    result={k:JP_REVERSE.get(v,v) if isinstance(v,str) and k not in {'base_url','api_key','model','voice_draft','voice_status'} else v for k,v in changes.items()};reverse={v:k for k,v in CHOICES.items()}
    for name,value in result.items():
        if not isinstance(value,str):continue
        if name in {'base_url','api_key','model','voice_draft','voice_status'}:continue
        if name=='interface_language':result[name]={'Simplified Chinese':'简体中文'}.get(value,value)
        elif name=='speech_voice':result[name]={'Chinese':'中文','English':'英文','Automatic (Chinese/English)':'自动（中英）'}.get(value,value)
        elif name=='selected_conversation':
            value=value.replace('ピン留め · ','Pinned · ',1).replace('最近 · ','Recent · ',1)
            result[name]=value.replace('Pinned · ','置顶 · ',1) if value.startswith('Pinned · ') else value.replace('Recent · ','最近 · ',1)
        elif name=='default_mode':result[name]={'Voice conversation':'talk','Read replies':'reply','Completion alerts':'notify'}.get(value,value)
        elif name=='summary_length':result[name]={'Short':'short','Normal':'normal'}.get(value,value)
        else:result[name]=reverse.get(value,value)
    return result
