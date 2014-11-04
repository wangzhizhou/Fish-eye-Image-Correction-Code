#include "panoramaExpansion.h"	

Mat panoramaExpansion(Mat imgOrg, Point center, int radius, double startRadian, CorrectType type)
{
	//设定展开图的高度，因为鱼眼图像不能灰复高度信息，所以这里可以跟根实际来
	//进行调节
	int heightOfPanorama=radius*2;

	//设定展开图的宽度，这里设定为鱼眼图像圆形有效区域的周长
	int widthOfPanorama=2*PI*radius;


	double dx = 2*PI/widthOfPanorama;
	double dy = radius / (double)heightOfPanorama;

	double p;
	double theta;

	double x, y;

	int u, v;

	//展开图的变量分配
	Mat retImg(heightOfPanorama,widthOfPanorama, CV_8UC3, Scalar(0, 0, 0));
	Mat_<Vec3b> _retImg = retImg;
	Mat_<Vec3b> _imgOrg = imgOrg.clone();

	switch (type)
	{
	case Reverse:	//使用反向映射来填充展开图
		for (int j = 0; j < heightOfPanorama; j++)
		{
			for (int i = 0; i < widthOfPanorama; i++)
			{
				p = j*dy;
				theta = i*dx + startRadian;

				x = p*cos(theta);
				y = p*sin(theta);

				u = x + center.x;
				v = y + center.y;

				_retImg(j, i)[0] = _imgOrg(v, u)[0];
				_retImg(j, i)[1] = _imgOrg(v, u)[1];
				_retImg(j, i)[2] = _imgOrg(v, u)[2];

			}
		}
		break;

	case Forward:
		int left, top;
		left = center.x - radius;
		top = center.y - radius;
		for (int j = top; j < top + 2 * radius; j++)
		{
			for (int i = left; i < left + 2 * radius; i++)
			{
				if (pow(i - center.x, 2) + pow(j - center.y, 2)>pow(radius, 2))
					continue;

				u = i;
				v = j;

				x = (u - center.x) ;
				y = -(v - center.y);

				//convert to polar axes
				theta = cvFastArctan(y, x)*PI / 180;
				p = sqrt(pow(x, 2) + pow(y, 2));				

				theta -= startRadian;
				theta = theta < 0 ? theta + 2 * PI : theta;

				int u_ret = theta / dx;
				int v_ret = p / dy;	

				if (u_ret<0 || u_ret >= widthOfPanorama || v_ret<0 || v_ret >= heightOfPanorama)
					continue;

				//perform the map from the origin image to the latitude map image
				_retImg(v_ret, u_ret)[0] = _imgOrg(j, i)[0];
				_retImg(v_ret, u_ret)[1] = _imgOrg(j, i)[1];
				_retImg(v_ret, u_ret)[2] = _imgOrg(j, i)[2];
			}
		}

		break;
	}
	
#ifdef _DEBUG_
	namedWindow("expand fish-eye image",CV_WINDOW_AUTOSIZE);
	imshow("expand fish-eye image",retImg);
	waitKey();
#endif
	return	retImg;
}