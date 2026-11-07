# KITTI 注册与图像获取步骤

已核实两个官方公开页面：[访问要求](https://www.cvlibs.net/datasets/kitti/user_login.php)、[注册表单](https://www.cvlibs.net/datasets/kitti/user_register.php)。下载数据只需要下载注册及邮件激活，无需申请排行榜提交资格。本轮只读取了页面，没有注册、发送邮件或下载数据。

## 1. 在官网填写下载注册

打开上面的注册表单，填写下载注册部分：

| 字段 | 如何填写 |
|---|---|
| First Name / Last Name | 真实名字 / 姓氏 |
| Organization | 实际所属机构 |
| Url | 实际使用的个人或机构网址；页面未说明没有网址时应如何填写 |
| Email | 本人可接收邮件的机构邮箱；页面未确认个人邮箱是否可用 |
| Choose Password / Re-enter Password | 在官网自行设置并重复输入密码，不发到聊天中 |
| Purpose of download | 简明的2–3句实际用途；表单上限1000字符 |

用途草稿如下，可按实际研究安排修改后使用；它没有假定你的机构或商业属性：

> I am studying LiDAR point-cloud registration and loop-closure verification. I plan to use the KITTI odometry images, LiDAR scans and calibration for offline camera–LiDAR correspondence analysis and comparisons with geometric baselines.

填写完核对信息后，按官网说明仅提交一次。随后自行查看注册邮箱和垃圾邮件文件夹，通过官方确认邮件中的链接激活。页面预计数分钟送达，但本轮未验证邮件流程或送达时间。仅下载数据时无需继续填写排行榜提交申请。

## 2. 激活后获取里程计灰度图像

自行登录官网并进入[里程计页面](https://www.cvlibs.net/datasets/kitti/eval_odometry.php)，选择里程计灰度图像数据。2026-10-26保存的官方页面标注约22GB；这是整套下载的历史页面标注，不是本项目273帧子集的实测体积。无需为本次准备任务另取彩色图像或重新下载已有的LiDAR、参考位姿、模型。

保留原始下载压缩包及合法来源记录，包括实际发布/下载入口、下载日期、原始文件名、发布版本或标识（若提供）和下载完成状态。不要在记录或聊天中粘贴密码、Cookie、激活链接或含登录令牌的地址。账号提交、激活和数据下载尚未由本轮执行；本指南也没有授权自动开始22GB传输。

## 3. 项目只需要完整273帧相机0图像

具体名单在同目录 REQUIRED_CAMERA0_MEMBERS.txt 和 CAMERA_REQUEST_MANIFEST.json。它由既有200个F2配对完整导出，不按支持度或历史结果筛选。覆盖序列00和08，均使用image_0。清单中的dataset/sequences/...是项目期望成员路径，新压缩包的实际成员前缀仍待核实。

下载完成后，给出原压缩包或合法解压目录的本地完整路径即可。下一步先核对来源、完整273成员、缺失/重复、PNG尺寸和标定/时间关联，再单独确定图像实验；不需要把全部数据上传到聊天中。暂时保留原压缩包，避免重命名成员或只保留视觉上匹配良好的配对。

取得图像仍只是数据条件。原200配对已经暴露，不能据此宣称独立泛化；先比较普通视觉几何和明确的RAP初始化作用，并保留无证据回退。此前约1.98%的拟合损失下降及完整噪声门槛失败保持原结论。
